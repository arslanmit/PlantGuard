# Mobile PlantGuard Deployment Guide

This directory contains all the necessary files and configurations for deploying the Mobile PlantGuard application in production and development environments.

## Quick Start

### Prerequisites

- Docker 20.10+
- Docker Compose 2.0+
- 4GB+ RAM available
- 10GB+ disk space

### Basic Deployment

```bash
# Clone the repository
git clone <repository-url>
cd PlantGuard

# Deploy in production mode
./deployment/deploy.sh

# Access the application
open http://localhost:8501
```

### Development Deployment

```bash
# Deploy in development mode with hot reload
./deployment/deploy.sh -e development
```

## Deployment Options

### Environment Modes

#### Production Mode (Default)
- Optimized for performance and security
- Minimal logging
- Resource limits enforced
- HTTPS enabled (if certificates available)
- Caching enabled

```bash
./deployment/deploy.sh -e production
```

#### Development Mode
- Hot reload enabled
- Detailed logging
- Development tools included
- Source code mounted as volumes
- Debug mode enabled

```bash
./deployment/deploy.sh -e development
```

### Deployment Scripts

#### Main Deployment Script
```bash
./deployment/deploy.sh [OPTIONS]

Options:
  -e, --env ENVIRONMENT    Set deployment environment (development|production)
  -h, --help              Show help message
  --build-only            Only build images, don't start services
  --no-health-check       Skip health checks
```

#### Management Scripts
```bash
# Stop all services
docker-compose -f deployment/docker-compose.mobile.yml down

# View logs
docker-compose -f deployment/docker-compose.mobile.yml logs -f

# Restart services
docker-compose -f deployment/docker-compose.mobile.yml restart

# Update and redeploy
./deployment/deploy.sh --build-only
docker-compose -f deployment/docker-compose.mobile.yml up -d
```

## Configuration Files

### Core Configuration

#### `mobile_deployment_config.yaml`
Main configuration file containing:
- Application settings
- Mobile optimization parameters
- Security configuration
- Resource limits
- Monitoring settings

#### `Dockerfile.mobile`
Multi-stage Docker build file:
- Builder stage: Installs dependencies and builds application
- Production stage: Optimized runtime environment
- Development stage: Development tools and hot reload

#### `docker-compose.mobile.yml`
Docker Compose configuration:
- Main application service
- Nginx reverse proxy
- Redis cache (optional)
- Volume and network configuration

### Nginx Configuration

#### `nginx/mobile.conf`
Nginx reverse proxy configuration:
- Mobile-optimized settings
- Gzip compression
- Static asset caching
- WebSocket support for streamlit-webrtc
- Security headers
- Rate limiting

### Monitoring Configuration

#### `monitoring/prometheus_config.yml`
Prometheus monitoring configuration:
- Scrape configurations for all services
- Mobile-specific metrics collection
- Alert rule integration

#### `monitoring/mobile_alert_rules.yml`
Prometheus alert rules:
- Application availability alerts
- Performance alerts
- Resource usage alerts
- Component-specific alerts
- Security alerts

#### `monitoring/grafana_dashboard.json`
Grafana dashboard configuration:
- Application metrics visualization
- Performance monitoring
- Error tracking
- User experience metrics

## Architecture Overview

### Service Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Nginx Proxy   │────│  PlantGuard     │────│  Redis Cache    │
│   (Port 80/443) │    │  Mobile App     │    │  (Optional)     │
│                 │    │  (Port 8501)    │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
    ┌─────────┐            ┌─────────┐            ┌─────────┐
    │ Static  │            │  Model  │            │  Temp   │
    │ Assets  │            │  Files  │            │  Files  │
    └─────────┘            └─────────┘            └─────────┘
```

### Container Architecture

- **plantguard-mobile**: Main Streamlit application
- **nginx-mobile**: Reverse proxy with mobile optimizations
- **redis-cache**: Optional caching layer for improved performance

### Volume Management

- **Model Storage**: Persistent storage for ML models
- **Log Storage**: Application and access logs
- **Temporary Files**: Session-based temporary file storage
- **Cache Storage**: Redis data persistence

## Mobile Optimizations

### Performance Optimizations

1. **Nginx Configuration**:
   - Gzip compression for text assets
   - Static asset caching with appropriate TTL
   - Connection keep-alive optimization
   - Request buffering for large uploads

2. **Application Level**:
   - Lazy loading of components
   - Image compression and optimization
   - Model caching with `@st.cache_resource`
   - Session state optimization

3. **Docker Optimizations**:
   - Multi-stage builds for smaller images
   - Layer caching optimization
   - Resource limits to prevent memory issues
   - Health checks for reliability

### Mobile-Specific Features

1. **Touch Optimization**:
   - Minimum 48px touch targets
   - Touch-action CSS properties
   - Haptic feedback support
   - Gesture recognition

2. **Responsive Design**:
   - Mobile-first CSS approach
   - Flexible grid layouts
   - Viewport meta tag optimization
   - Device-specific breakpoints

3. **Offline Capability**:
   - Local model storage
   - Service worker caching
   - Offline detection
   - Graceful degradation

## Security Configuration

### Application Security

1. **HTTPS Configuration**:
   - SSL/TLS termination at Nginx
   - HTTP to HTTPS redirection
   - HSTS headers
   - Secure cookie settings

2. **Content Security Policy**:
   - Restrictive CSP headers
   - XSS protection
   - Frame options
   - Content type validation

3. **Rate Limiting**:
   - API endpoint rate limiting
   - Upload endpoint restrictions
   - DDoS protection
   - Suspicious activity detection

### Container Security

1. **Non-root User**:
   - Application runs as non-root user
   - Proper file permissions
   - Security context constraints

2. **Resource Limits**:
   - Memory limits to prevent OOM
   - CPU limits for fair resource sharing
   - Disk space monitoring
   - Network isolation

## Monitoring and Observability

### Health Checks

The deployment includes comprehensive health checks:

1. **Application Health**: `/health` endpoint
2. **Container Health**: Docker health checks
3. **Service Dependencies**: Database and cache connectivity
4. **Resource Monitoring**: CPU, memory, disk usage

### Metrics Collection

1. **Application Metrics**:
   - Request rates and response times
   - Error rates and types
   - Feature usage statistics
   - User interaction patterns

2. **Infrastructure Metrics**:
   - Container resource usage
   - Network traffic patterns
   - Storage utilization
   - Service availability

3. **Business Metrics**:
   - Analysis success rates
   - User engagement metrics
   - Performance benchmarks
   - Error recovery rates

### Alerting

Configured alerts for:
- Application downtime
- High error rates
- Performance degradation
- Resource exhaustion
- Security incidents

## Troubleshooting

### Common Issues

#### Application Won't Start

```bash
# Check container logs
docker-compose -f deployment/docker-compose.mobile.yml logs plantguard-mobile

# Check container status
docker ps -a

# Verify configuration
docker-compose -f deployment/docker-compose.mobile.yml config
```

#### Performance Issues

```bash
# Monitor resource usage
docker stats

# Check application metrics
curl http://localhost:8501/metrics

# Review nginx logs
docker-compose -f deployment/docker-compose.mobile.yml logs nginx-mobile
```

#### Network Issues

```bash
# Test connectivity
curl -I http://localhost:8501/health

# Check port bindings
docker port plantguard-mobile

# Verify nginx configuration
docker exec plantguard-nginx-mobile nginx -t
```

### Log Analysis

#### Application Logs
```bash
# Real-time application logs
docker-compose -f deployment/docker-compose.mobile.yml logs -f plantguard-mobile

# Search for errors
docker-compose -f deployment/docker-compose.mobile.yml logs plantguard-mobile | grep ERROR
```

#### Access Logs
```bash
# Nginx access logs
docker-compose -f deployment/docker-compose.mobile.yml logs nginx-mobile

# Filter by status code
docker-compose -f deployment/docker-compose.mobile.yml logs nginx-mobile | grep "HTTP/1.1\" 5"
```

### Performance Tuning

#### Memory Optimization
```bash
# Adjust memory limits in docker-compose.mobile.yml
deploy:
  resources:
    limits:
      memory: 4G  # Increase if needed
```

#### CPU Optimization
```bash
# Adjust CPU limits
deploy:
  resources:
    limits:
      cpus: '2.0'  # Increase for better performance
```

## Backup and Recovery

### Data Backup

1. **Model Files**: Backup `data/models/` directory
2. **Configuration**: Backup all configuration files
3. **Logs**: Archive log files periodically
4. **User Data**: No persistent user data (privacy by design)

### Recovery Procedures

1. **Application Recovery**:
   ```bash
   # Stop services
   docker-compose -f deployment/docker-compose.mobile.yml down
   
   # Restore configuration
   git checkout -- deployment/
   
   # Redeploy
   ./deployment/deploy.sh
   ```

2. **Data Recovery**:
   ```bash
   # Restore model files
   cp -r backup/models/* data/models/
   
   # Restart services
   docker-compose -f deployment/docker-compose.mobile.yml restart
   ```

## Scaling and Load Balancing

### Horizontal Scaling

To scale the application horizontally:

```bash
# Scale application containers
docker-compose -f deployment/docker-compose.mobile.yml up -d --scale plantguard-mobile=3

# Update nginx configuration for load balancing
# Edit nginx/mobile.conf to include multiple upstream servers
```

### Vertical Scaling

```bash
# Increase resource limits in docker-compose.mobile.yml
deploy:
  resources:
    limits:
      memory: 8G
      cpus: '4.0'
```

## Production Checklist

Before deploying to production:

- [ ] SSL certificates configured
- [ ] Environment variables set
- [ ] Resource limits configured
- [ ] Monitoring enabled
- [ ] Backup procedures tested
- [ ] Security scan completed
- [ ] Performance testing done
- [ ] Health checks verified
- [ ] Documentation updated
- [ ] Team training completed

## Support and Maintenance

### Regular Maintenance Tasks

1. **Weekly**:
   - Review application logs
   - Check resource usage
   - Update security patches
   - Backup configuration

2. **Monthly**:
   - Performance analysis
   - Security audit
   - Dependency updates
   - Capacity planning

3. **Quarterly**:
   - Full system backup
   - Disaster recovery testing
   - Performance benchmarking
   - Architecture review

### Getting Help

1. **Documentation**: Check this README and component documentation
2. **Logs**: Review application and container logs
3. **Monitoring**: Check Grafana dashboards and Prometheus alerts
4. **Community**: Consult PlantGuard community forums
5. **Support**: Contact the development team

For additional support or questions, please refer to the [Mobile PlantGuard Complete Guide](../docs/MOBILE_PLANTGUARD_COMPLETE_GUIDE.md) or contact the development team.