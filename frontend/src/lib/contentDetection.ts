/**
 * Content Detection Utilities
 * Detects images, mathematical expressions, and blueprints in uploaded files
 */

export type DetectedContentType = 'image' | 'mathematical' | 'blueprint' | null;

export interface ContentDetectionResult {
  type: DetectedContentType;
  confidence: number;
  details: string;
}

/**
 * Detect content type from file name and extension
 */
export function detectContentFromFileName(fileName: string): ContentDetectionResult {
  const lowerFileName = fileName.toLowerCase();
  
  // Image detection
  const imageExtensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp', '.svg'];
  const isImage = imageExtensions.some(ext => lowerFileName.endsWith(ext));
  
  if (isImage) {
    return {
      type: 'image',
      confidence: 0.9,
      details: `Detected image file: ${fileName}`
    };
  }
  
  // Blueprint/technical drawing detection
  const blueprintKeywords = [
    'blueprint', 'drawing', 'schematic', 'diagram', 'plan', 'layout', 'technical',
    'engineering', 'architectural', 'floorplan', 'circuit', 'wiring', 'mechanical'
  ];
  
  const hasBlueprintKeywords = blueprintKeywords.some(keyword => 
    lowerFileName.includes(keyword)
  );
  
  if (hasBlueprintKeywords) {
    return {
      type: 'blueprint',
      confidence: 0.8,
      details: `Detected blueprint/technical content in filename: ${fileName}`
    };
  }
  
  // Mathematical expression detection in filename
  const mathPatterns = [
    /\d+x\d+/i,  // 25X54 pattern
    /\d+\s*[+\-*/]\s*\d+/,  // Basic arithmetic
    /\d+\s*[=]\s*\d+/,  // Equations
    /[a-zA-Z]\s*[=]\s*\d+/,  // Variable assignments
    /\d+\s*[%]/,  // Percentages
    /sqrt|log|sin|cos|tan|exp/,  // Mathematical functions
  ];
  
  const hasMathPatterns = mathPatterns.some(pattern => pattern.test(fileName));
  
  if (hasMathPatterns) {
    return {
      type: 'mathematical',
      confidence: 0.7,
      details: `Detected mathematical expressions in filename: ${fileName}`
    };
  }
  
  return {
    type: null,
    confidence: 0,
    details: 'No special content detected'
  };
}

/**
 * Detect content type from file content (for text-based files)
 */
export async function detectContentFromFileContent(file: File): Promise<ContentDetectionResult> {
  // Only process text-based files
  const textExtensions = ['.txt', '.md', '.csv', '.json', '.xml', '.html', '.htm'];
  const lowerFileName = file.name.toLowerCase();
  const isTextFile = textExtensions.some(ext => lowerFileName.endsWith(ext));
  
  if (!isTextFile) {
    return {
      type: null,
      confidence: 0,
      details: 'Not a text file, skipping content analysis'
    };
  }
  
  try {
    const text = await file.text();
    const lowerText = text.toLowerCase();
    
    // Mathematical expression detection in content
    const mathPatterns = [
      /\d+\s*[+\-*/]\s*\d+/,  // Basic arithmetic
      /\d+\s*[=]\s*\d+/,  // Equations
      /[a-zA-Z]\s*[=]\s*\d+/,  // Variable assignments
      /\d+\s*[%]/,  // Percentages
      /sqrt|log|sin|cos|tan|exp/,  // Mathematical functions
      /\d+\s*x\s*\d+/i,  // 25X54 pattern
      /[a-zA-Z]\s*[+\-*/]\s*[a-zA-Z]/,  // Variable arithmetic
      /\d+\.\d+\s*[+\-*/]\s*\d+\.\d+/,  // Decimal arithmetic
    ];
    
    const mathMatches = mathPatterns.filter(pattern => pattern.test(text));
    
    if (mathMatches.length > 0) {
      return {
        type: 'mathematical',
        confidence: Math.min(0.9, 0.5 + (mathMatches.length * 0.1)),
        details: `Detected ${mathMatches.length} mathematical expressions in content`
      };
    }
    
    // Blueprint/technical content detection
    const blueprintKeywords = [
      'blueprint', 'drawing', 'schematic', 'diagram', 'plan', 'layout', 'technical',
      'engineering', 'architectural', 'floorplan', 'circuit', 'wiring', 'mechanical',
      'dimension', 'scale', 'measurement', 'specification', 'technical drawing'
    ];
    
    const blueprintMatches = blueprintKeywords.filter(keyword => 
      lowerText.includes(keyword)
    );
    
    if (blueprintMatches.length > 0) {
      return {
        type: 'blueprint',
        confidence: Math.min(0.9, 0.6 + (blueprintMatches.length * 0.05)),
        details: `Detected ${blueprintMatches.length} blueprint/technical keywords in content`
      };
    }
    
    return {
      type: null,
      confidence: 0,
      details: 'No special content detected in file content'
    };
    
  } catch (error) {
    console.error('Error reading file content for detection:', error);
    return {
      type: null,
      confidence: 0,
      details: 'Error reading file content'
    };
  }
}

/**
 * Main detection function that combines filename and content analysis
 */
export async function detectContentType(file: File): Promise<ContentDetectionResult> {
  // First check filename
  const fileNameResult = detectContentFromFileName(file.name);
  
  // If we have a high confidence result from filename, return it
  if (fileNameResult.confidence > 0.7) {
    return fileNameResult;
  }
  
  // Otherwise, analyze file content
  const contentResult = await detectContentFromFileContent(file);
  
  // Return the result with higher confidence
  if (contentResult.confidence > fileNameResult.confidence) {
    return contentResult;
  }
  
  return fileNameResult;
}

/**
 * Check if content should trigger model selection modal
 */
export function shouldShowModelSelection(detectionResult: ContentDetectionResult): boolean {
  return detectionResult.type !== null && detectionResult.confidence > 0.6;
}
