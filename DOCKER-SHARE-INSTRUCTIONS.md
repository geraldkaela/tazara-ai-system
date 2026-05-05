# 🐳 TAZARA AI Railway System - Docker Setup

## 🚀 Quick Start for Your Friend

Your friend can run the entire TAZARA system with these simple commands:

### 1. Prerequisites
- Install [Docker Desktop](https://www.docker.com/products/docker-desktop/) (Windows/Mac) or Docker (Linux)

### 2. Download and Run
```bash
# Download the project files (you'll share these)
# Extract to a folder, then run:

docker-compose -f docker-compose-simple.yml up --build
```

### 3. Access the System
- **Main Dashboard**: http://localhost:80/multi_route.html
- **API Documentation**: http://localhost:8000/docs
- **Alerts**: http://localhost:80/alerts.html

### 4. Stop the System
```bash
docker-compose -f docker-compose-simple.yml down
```

## 📦 What to Share

Share these files/folders with your friend:
```
tazara-ai-system/
├── Dockerfile
├── docker-compose-simple.yml
├── requirements.txt
├── api/
├── dashboard/
├── reinforcement_rl/
├── database/
└── nginx/
```

## 🎯 What's Included

- ✅ PostgreSQL Database (pre-configured)
- ✅ Backend API (FastAPI)
- ✅ Frontend Dashboard (HTML/CSS/JS)
- ✅ Reinforcement Learning Models
- ✅ All TAZARA routes and stations
- ✅ Multi-route scheduling system

## 🔧 Troubleshooting

**Port Already in Use?**
```bash
# Change ports in docker-compose-simple.yml
ports:
  - "8080:80"  # Instead of "80:80"
```

**Database Connection Issues?**
```bash
# Reset database
docker-compose -f docker-compose-simple.yml down -v
docker-compose -f docker-compose-simple.yml up --build
```

## 📞 Support

If your friend has issues, they can:
1. Check Docker Desktop is running
2. Ensure ports 80, 8000, 5432 are available
3. Run `docker-compose logs` to see error messages

## 🚂 Ready to Go!

The system includes sample data and all TAZARA routes. Your friend can immediately:
- Create customer orders
- Generate train schedules
- View performance analytics
- Use the RL optimization features

**No setup required - just Docker and run!** 🎉
