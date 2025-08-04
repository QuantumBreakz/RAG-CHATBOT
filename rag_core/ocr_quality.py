"""
OCR Quality Assessment and Reporting System

This module provides comprehensive quality assessment, metrics tracking, and reporting
for the multi-OCR pipeline to ensure high accuracy and identify areas for improvement.
"""

import time
import json
import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
import statistics
from collections import defaultdict, Counter

from .multi_ocr import OCRConfidence, ConsensusResult, OCRResult

logger = logging.getLogger(__name__)

@dataclass
class QualityMetrics:
    """Quality metrics for OCR processing"""
    # Processing metrics
    total_documents: int
    successful_documents: int
    failed_documents: int
    total_pages: int
    successful_pages: int
    failed_pages: int
    
    # Confidence metrics
    high_confidence_pages: int
    medium_confidence_pages: int
    low_confidence_pages: int
    rejected_pages: int
    
    # Performance metrics
    total_processing_time: float
    average_processing_time_per_page: float
    average_processing_time_per_document: float
    
    # Accuracy metrics
    average_agreement_score: float
    average_confidence_score: float
    inter_engine_agreement_rate: float
    
    # Quality flags
    total_quality_flags: int
    quality_flag_distribution: Dict[str, int]
    
    # Engine performance
    engine_usage_stats: Dict[str, Dict[str, Any]]
    
    # Error analysis
    error_distribution: Dict[str, int]
    common_error_patterns: List[str]

@dataclass
class DocumentQualityReport:
    """Quality report for a single document"""
    filename: str
    file_size: int
    document_type: str
    processing_time: float
    confidence_level: OCRConfidence
    agreement_score: float
    quality_flags: List[str]
    engine_results: List[OCRResult]
    consensus_result: ConsensusResult
    metadata: Dict[str, Any]

class OCRQualityAssessor:
    """Quality assessment and reporting system for multi-OCR pipeline"""
    
    def __init__(self, output_dir: str = "ocr_quality_reports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.metrics_history: List[QualityMetrics] = []
        self.document_reports: List[DocumentQualityReport] = []
        
    def assess_document_quality(self, filename: str, file_size: int, 
                              engine_results: List[OCRResult], 
                              consensus_result: ConsensusResult,
                              document_type: str = "unknown") -> DocumentQualityReport:
        """
        Assess quality of OCR processing for a single document.
        
        Args:
            filename: Name of the processed file
            file_size: Size of the file in bytes
            engine_results: Results from individual OCR engines
            consensus_result: Final consensus result
            document_type: Type of document (legal, medical, etc.)
            
        Returns:
            DocumentQualityReport with quality assessment
        """
        # Analyze engine performance
        engine_stats = self._analyze_engine_performance(engine_results)
        
        # Identify quality flags
        quality_flags = self._identify_quality_flags(engine_results, consensus_result)
        
        # Create report
        report = DocumentQualityReport(
            filename=filename,
            file_size=file_size,
            document_type=document_type,
            processing_time=consensus_result.processing_time,
            confidence_level=consensus_result.confidence,
            agreement_score=consensus_result.agreement_score,
            quality_flags=quality_flags,
            engine_results=engine_results,
            consensus_result=consensus_result,
            metadata={
                "num_engines_used": len(engine_results),
                "engines_used": [r.engine_name for r in engine_results],
                "best_engine": consensus_result.metadata.get("best_engine", "unknown"),
                "best_confidence": consensus_result.metadata.get("best_confidence", 0.0),
                "avg_similarity": consensus_result.metadata.get("avg_similarity", 0.0)
            }
        )
        
        self.document_reports.append(report)
        return report
    
    def _analyze_engine_performance(self, engine_results: List[OCRResult]) -> Dict[str, Dict[str, Any]]:
        """Analyze performance of individual OCR engines"""
        engine_stats = {}
        
        for result in engine_results:
            engine_name = result.engine_name
            if engine_name not in engine_stats:
                engine_stats[engine_name] = {
                    "total_runs": 0,
                    "successful_runs": 0,
                    "failed_runs": 0,
                    "total_processing_time": 0.0,
                    "average_confidence": 0.0,
                    "total_text_length": 0,
                    "errors": []
                }
            
            stats = engine_stats[engine_name]
            stats["total_runs"] += 1
            stats["total_processing_time"] += result.processing_time
            
            if result.text.strip():
                stats["successful_runs"] += 1
                stats["total_text_length"] += len(result.text)
                stats["average_confidence"] = (
                    (stats["average_confidence"] * (stats["successful_runs"] - 1) + result.confidence) / 
                    stats["successful_runs"]
                )
            else:
                stats["failed_runs"] += 1
                if "error" in result.metadata:
                    stats["errors"].append(result.metadata["error"])
        
        return engine_stats
    
    def _identify_quality_flags(self, engine_results: List[OCRResult], 
                               consensus_result: ConsensusResult) -> List[str]:
        """Identify quality issues in OCR processing"""
        flags = []
        
        # Check for engine failures
        failed_engines = [r for r in engine_results if not r.text.strip()]
        if failed_engines:
            flags.append(f"engine_failures:{len(failed_engines)}")
        
        # Check for low confidence
        if consensus_result.confidence == OCRConfidence.LOW:
            flags.append("low_confidence")
        elif consensus_result.confidence == OCRConfidence.REJECTED:
            flags.append("rejected_text")
        
        # Check for low agreement
        if consensus_result.agreement_score < 0.5:
            flags.append("low_agreement")
        
        # Check for quality flags from consensus
        flags.extend(consensus_result.quality_flags)
        
        # Check for processing time issues
        if consensus_result.processing_time > 30.0:  # More than 30 seconds
            flags.append("slow_processing")
        
        return flags
    
    def calculate_batch_metrics(self, reports: List[DocumentQualityReport]) -> QualityMetrics:
        """
        Calculate comprehensive quality metrics for a batch of documents.
        
        Args:
            reports: List of document quality reports
            
        Returns:
            QualityMetrics with batch statistics
        """
        if not reports:
            return QualityMetrics(
                total_documents=0, successful_documents=0, failed_documents=0,
                total_pages=0, successful_pages=0, failed_pages=0,
                high_confidence_pages=0, medium_confidence_pages=0, 
                low_confidence_pages=0, rejected_pages=0,
                total_processing_time=0.0, average_processing_time_per_page=0.0,
                average_processing_time_per_document=0.0, average_agreement_score=0.0,
                average_confidence_score=0.0, inter_engine_agreement_rate=0.0,
                total_quality_flags=0, quality_flag_distribution={},
                engine_usage_stats={}, error_distribution={}, common_error_patterns=[]
            )
        
        # Basic counts
        total_documents = len(reports)
        successful_documents = len([r for r in reports if r.confidence_level != OCRConfidence.REJECTED])
        failed_documents = total_documents - successful_documents
        
        # Page-level metrics (assuming 1 page per document for simplicity)
        total_pages = total_documents
        successful_pages = successful_documents
        failed_pages = failed_documents
        
        # Confidence distribution
        confidence_counts = Counter([r.confidence_level for r in reports])
        high_confidence_pages = confidence_counts[OCRConfidence.HIGH]
        medium_confidence_pages = confidence_counts[OCRConfidence.MEDIUM]
        low_confidence_pages = confidence_counts[OCRConfidence.LOW]
        rejected_pages = confidence_counts[OCRConfidence.REJECTED]
        
        # Processing time metrics
        processing_times = [r.processing_time for r in reports]
        total_processing_time = sum(processing_times)
        average_processing_time_per_page = statistics.mean(processing_times) if processing_times else 0.0
        average_processing_time_per_document = average_processing_time_per_page  # 1:1 mapping
        
        # Agreement and confidence scores
        agreement_scores = [r.agreement_score for r in reports if r.agreement_score > 0]
        average_agreement_score = statistics.mean(agreement_scores) if agreement_scores else 0.0
        
        # Calculate average confidence score
        confidence_scores = []
        for r in reports:
            if r.confidence_level == OCRConfidence.HIGH:
                confidence_scores.append(0.9)  # High confidence range
            elif r.confidence_level == OCRConfidence.MEDIUM:
                confidence_scores.append(0.7)  # Medium confidence range
            elif r.confidence_level == OCRConfidence.LOW:
                confidence_scores.append(0.3)  # Low confidence range
            else:
                confidence_scores.append(0.0)  # Rejected
        
        average_confidence_score = statistics.mean(confidence_scores) if confidence_scores else 0.0
        
        # Inter-engine agreement rate
        agreements = [r.agreement_score for r in reports if r.agreement_score > 0.5]
        inter_engine_agreement_rate = len(agreements) / len(reports) if reports else 0.0
        
        # Quality flags analysis
        all_flags = []
        for r in reports:
            all_flags.extend(r.quality_flags)
        
        total_quality_flags = len(all_flags)
        quality_flag_distribution = Counter(all_flags)
        
        # Engine usage statistics
        engine_usage_stats = defaultdict(lambda: {
            "total_runs": 0,
            "successful_runs": 0,
            "failed_runs": 0,
            "total_processing_time": 0.0,
            "average_confidence": 0.0
        })
        
        for r in reports:
            for engine_result in r.engine_results:
                stats = engine_usage_stats[engine_result.engine_name]
                stats["total_runs"] += 1
                stats["total_processing_time"] += engine_result.processing_time
                
                if engine_result.text.strip():
                    stats["successful_runs"] += 1
                    # Update average confidence
                    current_avg = stats["average_confidence"]
                    stats["average_confidence"] = (
                        (current_avg * (stats["successful_runs"] - 1) + engine_result.confidence) / 
                        stats["successful_runs"]
                    )
                else:
                    stats["failed_runs"] += 1
        
        # Error analysis
        error_distribution = defaultdict(int)
        error_patterns = []
        
        for r in reports:
            for engine_result in r.engine_results:
                if "error" in engine_result.metadata:
                    error_msg = engine_result.metadata["error"]
                    error_distribution[error_msg] += 1
                    error_patterns.append(error_msg)
        
        common_error_patterns = [pattern for pattern, count in 
                               sorted(error_distribution.items(), key=lambda x: x[1], reverse=True)[:5]]
        
        return QualityMetrics(
            total_documents=total_documents,
            successful_documents=successful_documents,
            failed_documents=failed_documents,
            total_pages=total_pages,
            successful_pages=successful_pages,
            failed_pages=failed_pages,
            high_confidence_pages=high_confidence_pages,
            medium_confidence_pages=medium_confidence_pages,
            low_confidence_pages=low_confidence_pages,
            rejected_pages=rejected_pages,
            total_processing_time=total_processing_time,
            average_processing_time_per_page=average_processing_time_per_page,
            average_processing_time_per_document=average_processing_time_per_document,
            average_agreement_score=average_agreement_score,
            average_confidence_score=average_confidence_score,
            inter_engine_agreement_rate=inter_engine_agreement_rate,
            total_quality_flags=total_quality_flags,
            quality_flag_distribution=dict(quality_flag_distribution),
            engine_usage_stats=dict(engine_usage_stats),
            error_distribution=dict(error_distribution),
            common_error_patterns=common_error_patterns
        )
    
    def generate_quality_report(self, metrics: QualityMetrics, 
                              output_filename: str = None) -> str:
        """
        Generate a comprehensive quality report.
        
        Args:
            metrics: Quality metrics to report
            output_filename: Optional filename for the report
            
        Returns:
            Path to the generated report file
        """
        if output_filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"ocr_quality_report_{timestamp}.json"
        
        report_path = self.output_dir / output_filename
        
        # Create comprehensive report
        report = {
            "report_metadata": {
                "generated_at": datetime.now().isoformat(),
                "report_type": "ocr_quality_assessment",
                "version": "1.0"
            },
            "summary": {
                "total_documents_processed": metrics.total_documents,
                "success_rate": metrics.successful_documents / metrics.total_documents if metrics.total_documents > 0 else 0.0,
                "average_confidence": metrics.average_confidence_score,
                "average_agreement": metrics.average_agreement_score,
                "total_processing_time_hours": metrics.total_processing_time / 3600
            },
            "detailed_metrics": asdict(metrics),
            "recommendations": self._generate_recommendations(metrics),
            "performance_analysis": self._analyze_performance(metrics)
        }
        
        # Save report
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        logger.info(f"Quality report generated: {report_path}")
        return str(report_path)
    
    def _generate_recommendations(self, metrics: QualityMetrics) -> List[str]:
        """Generate recommendations based on quality metrics"""
        recommendations = []
        
        # Success rate recommendations
        success_rate = metrics.successful_documents / metrics.total_documents if metrics.total_documents > 0 else 0.0
        if success_rate < 0.8:
            recommendations.append("Consider improving image preprocessing for better OCR accuracy")
            recommendations.append("Review document quality and scanning settings")
        
        # Confidence recommendations
        if metrics.average_confidence_score < 0.7:
            recommendations.append("Consider using higher DPI settings for better text clarity")
            recommendations.append("Implement additional OCR engines for better consensus")
        
        # Agreement recommendations
        if metrics.average_agreement_score < 0.6:
            recommendations.append("OCR engines show low agreement - consider engine configuration")
            recommendations.append("Review preprocessing steps for consistency")
        
        # Performance recommendations
        if metrics.average_processing_time_per_page > 10.0:
            recommendations.append("Processing time is high - consider optimizing image preprocessing")
            recommendations.append("Review OCR engine configuration for speed vs accuracy trade-off")
        
        # Quality flag recommendations
        if metrics.total_quality_flags > metrics.total_documents * 0.3:
            recommendations.append("High number of quality flags - review document preparation")
            recommendations.append("Consider implementing additional validation steps")
        
        return recommendations
    
    def _analyze_performance(self, metrics: QualityMetrics) -> Dict[str, Any]:
        """Analyze performance patterns and trends"""
        analysis = {
            "performance_trends": {
                "success_rate_trend": "stable",  # Would need historical data
                "confidence_trend": "stable",
                "processing_time_trend": "stable"
            },
            "bottlenecks": [],
            "optimization_opportunities": []
        }
        
        # Identify bottlenecks
        if metrics.average_processing_time_per_page > 15.0:
            analysis["bottlenecks"].append("Slow OCR processing")
        
        if metrics.failed_documents > metrics.total_documents * 0.2:
            analysis["bottlenecks"].append("High failure rate")
        
        # Identify optimization opportunities
        if metrics.average_confidence_score > 0.8:
            analysis["optimization_opportunities"].append("High confidence allows for faster processing")
        
        if metrics.inter_engine_agreement_rate > 0.9:
            analysis["optimization_opportunities"].append("High agreement allows for single-engine fallback")
        
        return analysis
    
    def export_document_reports(self, output_filename: str = None) -> str:
        """
        Export detailed document-level reports.
        
        Args:
            output_filename: Optional filename for the export
            
        Returns:
            Path to the exported file
        """
        if output_filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"document_reports_{timestamp}.json"
        
        export_path = self.output_dir / output_filename
        
        # Convert reports to serializable format
        serializable_reports = []
        for report in self.document_reports:
            serializable_report = {
                "filename": report.filename,
                "file_size": report.file_size,
                "document_type": report.document_type,
                "processing_time": report.processing_time,
                "confidence_level": report.confidence_level.value,
                "agreement_score": report.agreement_score,
                "quality_flags": report.quality_flags,
                "metadata": report.metadata,
                "consensus_result": {
                    "text_length": len(report.consensus_result.text),
                    "confidence": report.consensus_result.confidence.value,
                    "contributing_engines": report.consensus_result.contributing_engines,
                    "agreement_score": report.consensus_result.agreement_score,
                    "quality_flags": report.consensus_result.quality_flags
                },
                "engine_results": [
                    {
                        "engine_name": r.engine_name,
                        "text_length": len(r.text),
                        "confidence": r.confidence,
                        "processing_time": r.processing_time,
                        "metadata": r.metadata
                    }
                    for r in report.engine_results
                ]
            }
            serializable_reports.append(serializable_report)
        
        # Save export
        with open(export_path, 'w') as f:
            json.dump(serializable_reports, f, indent=2, default=str)
        
        logger.info(f"Document reports exported: {export_path}")
        return str(export_path)
    
    def get_summary_statistics(self) -> Dict[str, Any]:
        """Get summary statistics for all processed documents"""
        if not self.document_reports:
            return {}
        
        metrics = self.calculate_batch_metrics(self.document_reports)
        
        return {
            "total_documents": metrics.total_documents,
            "success_rate": metrics.successful_documents / metrics.total_documents if metrics.total_documents > 0 else 0.0,
            "average_confidence": metrics.average_confidence_score,
            "average_agreement": metrics.average_agreement_score,
            "average_processing_time": metrics.average_processing_time_per_page,
            "confidence_distribution": {
                "high": metrics.high_confidence_pages,
                "medium": metrics.medium_confidence_pages,
                "low": metrics.low_confidence_pages,
                "rejected": metrics.rejected_pages
            },
            "top_quality_flags": dict(Counter(metrics.quality_flag_distribution).most_common(5)),
            "engine_performance": {
                engine: {
                    "success_rate": stats["successful_runs"] / stats["total_runs"] if stats["total_runs"] > 0 else 0.0,
                    "average_confidence": stats["average_confidence"],
                    "average_processing_time": stats["total_processing_time"] / stats["total_runs"] if stats["total_runs"] > 0 else 0.0
                }
                for engine, stats in metrics.engine_usage_stats.items()
            }
        } 