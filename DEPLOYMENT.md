# XOR RAG Chatbot - Production Deployment Guide

This guide covers deploying the enhanced XOR RAG Chatbot with production-ready features including dynamic query routing, hybrid search, source attribution, and domain filtering. **The system runs completely offline after initial setup.**

## 🚀 Quick Start

### Prerequisites
- **Docker and Docker Compose** (for containerized deployment)
- **16-32GB RAM** (recommended for large document collections)
- **50GB+ disk space** (for models and data)
- **NVIDIA GPU** (optional, for faster LLM inference)
- **Internet connection** (only for initial setup and model downloads)

### 1. Clone and Setup
```bash
git clone <https://github.com/QuantumBreakz/RAG-CHATBOTl>
cd RAG-CHATBOT-XOR
```

### 2. Environment Configuration
Create a `.env` file in the root directory:
```env
# Application Settings
LOG_LEVEL=INFO
LOG_FILE=log/xor_rag_app.log
APP_MODE=production

# Ollama Configuration
OLLAMA_BASE_URL=http://ollama:11434
OLLAMA_EMBEDDING_MODEL=nomic-embed-text
OLLAMA_LLM_MODEL=llama3.2:3b

# Document Processing
MAX_FILE_SIZE=157286400
CHUNK_SIZE=800
CHUNK_OVERLAP=200
N_RESULTS=5

# Vector Store
CHROMA_DB_PATH=demo-rag-chroma
CHROMA_COLLECTION_NAME=documents

# Caching
CACHE_TTL=86400
EMBEDDINGS_CACHE_PATH=log/global_embeddings

# Frontend
FRONTEND_ORIGIN=http://localhost:3000
```

### 3. Download All Dependencies (Internet Required)
```bash
# Install Python dependencies (all local, no external APIs)
pip install -r requirements.txt

# Pre-download sentence-transformers model (recommended for full offline use)
python -c "from sentence_transformers import CrossEncoder; CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')"

# Pull Ollama models (stored locally in Docker volumes)
docker run --rm -v ollama_data:/root/.ollama ollama/ollama:latest ollama pull llama3.2:3b
docker run --rm -v ollama_data:/root/.ollama ollama/ollama:latest ollama pull nomic-embed-text
```

### 4. Deploy (Fully Offline)
```bash
# Build and start all services
docker-compose up --build -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f
```

### 5. Verify Offline Operation
```bash
# Test that all services work without internet
curl http://localhost:8000/health/detailed

# Verify all components are local
# - LLM: LLaMA 3.2:3B via Ollama (local)
# - Embeddings: nomic-embed-text via Ollama (local)
# - Reranking: sentence-transformers cross-encoder (local)
# - Vector DB: ChromaDB (local)
# - Cache: Redis (local)
```

### 6. Verify Deployment
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- Health Check: http://localhost:8000/health/detailed
- Domains API: http://localhost:8000/domains
- ChromaDB: http://localhost:8001

### ✅ Offline Operation Confirmation
After setup, the system runs **completely offline** with:
- ✅ **Local LLM**: LLaMA 3.2:3B via Ollama
- ✅ **Local Embeddings**: nomic-embed-text via Ollama  
- ✅ **Local Reranking**: sentence-transformers cross-encoder
- ✅ **Local Vector DB**: ChromaDB with persistent storage
- ✅ **Local Caching**: Redis with persistent storage
- ✅ **No External APIs**: Zero cloud dependencies
- ✅ **No Internet Required**: All models and services local

## 📊 Production Features

### Dynamic Query Routing
The system automatically classifies queries and routes them to relevant documents:

```bash
# Example queries and their routing
"Section 304" → Law documents
"Electronegativity of chlorine" → Chemistry documents  
"Prayer times" → Religious documents
"Molecular weight of water" → Chemistry documents
"Penalty for theft" → Law documents
```

### Domain Filtering
Users can filter queries by specific domains:
- Law (⚖️)
- Chemistry (🧪)
- Physics (⚛️)
- Religion (🕊️)
- Medicine (🏥)
- Finance (💰)
- Engineering (⚙️)
- Education (📚)
- Government (🏛️)
- Technology (💻)

### Source Attribution
Every response includes detailed source information:
- Document title
- Page number
- Section number
- Domain classification
- Full attribution string

### Health Monitoring
Real-time system metrics available at `/health/detailed`:
- CPU usage
- Memory usage
- Disk usage
- Service health (Ollama, ChromaDB, Redis)

## 🔧 Advanced Configuration

### Performance Tuning

#### Memory Optimization
```env
# Increase Redis memory
REDIS_MAX_MEMORY=8gb
REDIS_MAX_MEMORY_POLICY=allkeys-lru

# ChromaDB settings
CHROMA_HNSW_M=16
CHROMA_HNSW_EF_CONSTRUCTION=200
```

#### Batch Processing
```env
# Document processing batch size
BATCH_SIZE=20
EMBEDDING_BATCH_SIZE=50
```

### Security Configuration

#### HTTPS Setup
```yaml
# docker-compose.yml
services:
  frontend:
    environment:
      - HTTPS=true
    volumes:
      - ./ssl:/etc/nginx/ssl
```

#### Access Control
```env
# Enable authentication (if needed)
ENABLE_AUTH=true
JWT_SECRET=your-secret-key
```

### Backup Configuration

#### Automated Backups
Create a backup script:
```bash
#!/bin/bash
# backup.sh
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/xor_rag"

# Backup ChromaDB
docker exec rag-chatbot-xor-chromadb-1 tar -czf /tmp/chroma_backup_$DATE.tar.gz /chroma/chroma
docker cp rag-chatbot-xor-chromadb-1:/tmp/chroma_backup_$DATE.tar.gz $BACKUP_DIR/

# Backup logs and embeddings
tar -czf $BACKUP_DIR/logs_backup_$DATE.tar.gz log/
tar -czf $BACKUP_DIR/embeddings_backup_$DATE.tar.gz demo-rag-chroma/

# Clean old backups (keep last 7 days)
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete
```

Add to crontab:
```bash
# Daily backup at 2 AM
0 2 * * * /path/to/backup.sh
```

## 📈 Scaling Considerations

### Horizontal Scaling
For high-traffic deployments:

```yaml
# docker-compose.yml
services:
  backend:
    deploy:
      replicas: 3
    environment:
      - REDIS_CLUSTER=true
  
  chromadb:
    deploy:
      replicas: 2
    volumes:
      - chroma_data:/chroma/chroma
```

### Load Balancing
```yaml
# nginx.conf
upstream backend {
    server backend:8000;
    server backend2:8000;
    server backend3:8000;
}

server {
    listen 80;
    location /api {
        proxy_pass http://backend;
    }
}
```

### Database Sharding
For very large document collections (>100,000 chunks):

```python
# rag_core/vectorstore.py
def get_sharded_collection(domain: str):
    """Get domain-specific collection for sharding."""
    collection_name = f"documents_{domain}"
    return chroma_client.get_or_create_collection(name=collection_name)
```

## 🧪 Testing

### Run Integration Tests
```bash
# Frontend tests
cd frontend
npm run test

# Backend tests
cd backend
python -m pytest tests/

# End-to-end tests
npm run test:e2e
```

### Performance Testing
```bash
# Load test with multiple documents
python scripts/load_test.py --documents 100 --queries 1000

# Memory usage test
python scripts/memory_test.py --ram 16gb
```

### Test Scenarios

#### Multi-Document Query Routing
1. Upload documents from different domains
2. Test domain-specific queries
3. Verify source attribution
4. Check domain filtering

#### Performance Benchmarks
- Document upload: <30s per document
- Query response: <2s average
- Memory usage: <8GB for 1000 documents
- Concurrent users: 50+ simultaneous

## 🔍 Monitoring

### Log Analysis
```bash
# Monitor application logs
tail -f log/xor_rag_app.log

# Search for errors
grep "ERROR" log/xor_rag_app.log

# Performance metrics
grep "Query time" log/xor_rag_app.log | awk '{print $NF}'
```

### Health Checks
```bash
# Check all services
curl http://localhost:8000/health/detailed

# Monitor specific service
curl http://localhost:8000/test_vectorstore
```

### Metrics Dashboard
Set up Prometheus + Grafana for detailed monitoring:
- Query latency
- Memory usage
- Document processing time
- Error rates
- Domain classification accuracy

## 🚨 Troubleshooting

### Common Issues

#### Ollama Connection Issues
```bash
# Check Ollama service
docker-compose logs ollama

# Restart Ollama
docker-compose restart ollama

# Verify model availability
curl http://localhost:11434/api/tags
```

#### ChromaDB Performance Issues
```bash
# Check ChromaDB status
curl http://localhost:8001/api/v1/heartbeat

# Restart ChromaDB
docker-compose restart chromadb

# Clear cache if needed
docker-compose exec chromadb rm -rf /chroma/chroma/*
```

#### Memory Issues
```bash
# Check memory usage
docker stats

# Increase memory limits
# In docker-compose.yml:
services:
  backend:
    deploy:
      resources:
        limits:
          memory: 8G
```

### Performance Optimization

#### Slow Query Response
1. Check Redis cache hit rate
2. Verify embedding model performance
3. Consider reducing chunk size
4. Enable GPU acceleration for Ollama

#### High Memory Usage
1. Reduce batch sizes
2. Enable memory-efficient embeddings
3. Implement document cleanup
4. Monitor for memory leaks

## 📚 Best Practices

### Document Management
- Use semantic chunking for structured documents
- Implement document versioning
- Regular cleanup of old documents
- Backup before major updates

### Security
- Use HTTPS in production
- Implement rate limiting
- Regular security updates
- Monitor for suspicious activity

### Performance
- Monitor system resources
- Use appropriate chunk sizes
- Implement caching strategies
- Regular performance testing

### Maintenance
- Daily backups
- Weekly health checks
- Monthly performance reviews
- Quarterly security audits

## 🔄 Updates and Migration

### Updating the System
```bash
# Pull latest changes
git pull origin main

# Rebuild containers
docker-compose down
docker-compose up --build -d

# Verify deployment
curl http://localhost:8000/health
```

### Data Migration
```bash
# Export current data
python scripts/export_data.py

# Import to new system
python scripts/import_data.py
```

### Version Compatibility
- Check model compatibility before updates
- Test with sample data
- Maintain backup before major updates
- Document breaking changes

## 📞 Support

For production support:
- Monitor system logs
- Check health endpoints
- Review performance metrics
- Contact development team for issues

### Emergency Procedures
1. **System Down**: Restart services with `docker-compose restart`
2. **Data Loss**: Restore from latest backup
3. **Performance Issues**: Check resource usage and scale accordingly
4. **Security Breach**: Isolate system and review logs

---

**Note**: This deployment guide covers the production-ready XOR RAG Chatbot with enhanced features. For development setup, see the main README.md file. 