#!/usr/bin/env python3
"""
KBI Labs Procurement Analyst Platform - Startup Script
Comprehensive startup and management script for the procurement platform
"""

import asyncio
import subprocess
import sys
import os
import time
import signal
import logging
from pathlib import Path
import uvicorn
from concurrent.futures import ThreadPoolExecutor
import webbrowser

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ProcurementPlatformManager:
    """Manages the procurement platform startup and operations"""
    
    def __init__(self):
        self.processes = {}
        self.is_running = False
        self.base_dir = Path(__file__).parent
        
    def check_dependencies(self):
        """Check if all required dependencies are installed"""
        logger.info("Checking dependencies...")
        
        required_packages = [
            'fastapi', 'uvicorn', 'aiohttp', 'beautifulsoup4', 
            'scikit-learn', 'pandas', 'numpy', 'streamlit'
        ]
        
        missing_packages = []
        
        for package in required_packages:
            try:
                __import__(package)
            except ImportError:
                missing_packages.append(package)
        
        if missing_packages:
            logger.error(f"Missing required packages: {missing_packages}")
            logger.info("Installing missing packages...")
            
            try:
                subprocess.check_call([
                    sys.executable, "-m", "pip", "install", 
                    *missing_packages
                ])
                logger.info("Dependencies installed successfully")
            except subprocess.CalledProcessError as e:
                logger.error(f"Failed to install dependencies: {e}")
                return False
        
        logger.info("All dependencies satisfied")
        return True
    
    def check_ml_models(self):
        """Ensure ML models are trained and available"""
        logger.info("Checking ML models...")
        
        models_dir = self.base_dir / "models"
        required_models = [
            "contract_success_model.pkl",
            "fraud_detection_model.pkl",
            "contract_success_scaler.pkl",
            "fraud_detection_scaler.pkl"
        ]
        
        missing_models = []
        for model_file in required_models:
            if not (models_dir / model_file).exists():
                missing_models.append(model_file)
        
        if missing_models:
            logger.warning(f"Missing ML models: {missing_models}")
            logger.info("Training ML models...")
            
            try:
                # Run ML training script
                result = subprocess.run([
                    sys.executable, "quick_start_ml_prototype.py"
                ], cwd=self.base_dir, capture_output=True, text=True)
                
                if result.returncode == 0:
                    logger.info("ML models trained successfully")
                else:
                    logger.error(f"ML training failed: {result.stderr}")
                    return False
                    
            except Exception as e:
                logger.error(f"Error training ML models: {e}")
                return False
        
        logger.info("ML models are ready")
        return True
    
    def start_api_server(self):
        """Start the main API server"""
        logger.info("Starting API server...")
        
        try:
            # Import the app
            sys.path.insert(0, str(self.base_dir))
            from procurement_analyst_app import app
            
            # Configure uvicorn
            config = uvicorn.Config(
                app=app,
                host="0.0.0.0",
                port=8000,
                log_level="info",
                reload=False
            )
            
            server = uvicorn.Server(config)
            
            # Run server in thread
            def run_server():
                asyncio.set_event_loop(asyncio.new_event_loop())
                asyncio.run(server.serve())
            
            executor = ThreadPoolExecutor(max_workers=1)
            self.processes['api_server'] = executor.submit(run_server)
            
            logger.info("API server started on http://localhost:8000")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start API server: {e}")
            return False
    
    def start_streamlit_dashboard(self):
        """Start the Streamlit ML dashboard"""
        logger.info("Starting Streamlit ML dashboard...")
        
        try:
            # Start streamlit in subprocess
            process = subprocess.Popen([
                sys.executable, "-m", "streamlit", "run", 
                "streamlit_ml_dashboard.py", 
                "--server.port", "8501",
                "--server.headless", "true",
                "--browser.gatherUsageStats", "false"
            ], cwd=self.base_dir)
            
            self.processes['streamlit'] = process
            logger.info("Streamlit dashboard started on http://localhost:8501")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start Streamlit dashboard: {e}")
            return False
    
    def wait_for_services(self):
        """Wait for services to be ready"""
        logger.info("Waiting for services to be ready...")
        
        import requests
        
        # Wait for API server
        for i in range(30):  # 30 second timeout
            try:
                response = requests.get("http://localhost:8000/health", timeout=1)
                if response.status_code == 200:
                    logger.info("API server is ready")
                    break
            except:
                pass
            time.sleep(1)
        else:
            logger.warning("API server did not respond within timeout")
        
        # Wait for Streamlit
        for i in range(20):  # 20 second timeout
            try:
                response = requests.get("http://localhost:8501", timeout=1)
                if response.status_code == 200:
                    logger.info("Streamlit dashboard is ready")
                    break
            except:
                pass
            time.sleep(1)
        else:
            logger.warning("Streamlit dashboard did not respond within timeout")
    
    def open_browser(self):
        """Open browser with platform interfaces"""
        logger.info("Opening browser...")
        
        # Open main platform
        webbrowser.open("http://localhost:8000")
        
        # Wait a moment then open dashboard
        time.sleep(2)
        webbrowser.open("http://localhost:8501")
        
        # Open API docs
        time.sleep(1)
        webbrowser.open("http://localhost:8000/api/docs")
    
    def start_all_services(self):
        """Start all platform services"""
        logger.info("🚀 Starting KBI Labs Procurement Analyst Platform...")
        
        # Check dependencies
        if not self.check_dependencies():
            logger.error("Dependency check failed")
            return False
        
        # Check ML models
        if not self.check_ml_models():
            logger.error("ML model check failed")
            return False
        
        # Start API server
        if not self.start_api_server():
            logger.error("Failed to start API server")
            return False
        
        # Start Streamlit dashboard
        if not self.start_streamlit_dashboard():
            logger.error("Failed to start Streamlit dashboard")
            return False
        
        # Wait for services
        self.wait_for_services()
        
        # Open browser
        self.open_browser()
        
        self.is_running = True
        logger.info("✅ KBI Labs Procurement Analyst Platform started successfully!")
        
        return True
    
    def stop_all_services(self):
        """Stop all platform services"""
        logger.info("Stopping all services...")
        
        # Stop processes
        for name, process in self.processes.items():
            try:
                if hasattr(process, 'terminate'):
                    process.terminate()
                elif hasattr(process, 'kill'):
                    process.kill()
                logger.info(f"Stopped {name}")
            except Exception as e:
                logger.error(f"Error stopping {name}: {e}")
        
        self.is_running = False
        logger.info("All services stopped")
    
    def show_status(self):
        """Show platform status"""
        print("\n" + "="*60)
        print("🎯 KBI Labs Procurement Analyst Platform")
        print("="*60)
        
        if self.is_running:
            print("Status: ✅ RUNNING")
            print("\nAvailable Interfaces:")
            print("• Main Platform: http://localhost:8000")
            print("• ML Dashboard:  http://localhost:8501")
            print("• API Docs:      http://localhost:8000/api/docs")
            print("• Health Check:  http://localhost:8000/health")
            
            print("\nKey Features:")
            print("• 🎯 Real-time Opportunity Intelligence")
            print("• 🤖 AI-Powered Contract Success Prediction")
            print("• 📊 Interactive ML Analytics Dashboard")
            print("• 🔍 Advanced Market Intelligence")
            print("• ⚡ Professional Procurement Tools")
            
        else:
            print("Status: ❌ NOT RUNNING")
        
        print("="*60 + "\n")
    
    def run_interactive(self):
        """Run in interactive mode"""
        self.show_status()
        
        if not self.is_running:
            if self.start_all_services():
                self.show_status()
            else:
                logger.error("Failed to start platform")
                return
        
        # Set up signal handlers
        def signal_handler(signum, frame):
            logger.info("Received shutdown signal")
            self.stop_all_services()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        try:
            print("Platform is running. Press Ctrl+C to stop.\n")
            
            while self.is_running:
                time.sleep(1)
                
        except KeyboardInterrupt:
            logger.info("Received KeyboardInterrupt")
        finally:
            self.stop_all_services()

def main():
    """Main entry point"""
    manager = ProcurementPlatformManager()
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "start":
            manager.start_all_services()
            if manager.is_running:
                manager.show_status()
                print("Platform started. Use 'python start_procurement_platform.py stop' to stop.")
        
        elif command == "stop":
            manager.stop_all_services()
            print("Platform stopped.")
        
        elif command == "status":
            manager.show_status()
        
        elif command == "restart":
            manager.stop_all_services()
            time.sleep(2)
            manager.start_all_services()
            if manager.is_running:
                manager.show_status()
        
        else:
            print("Usage: python start_procurement_platform.py [start|stop|status|restart]")
            print("       python start_procurement_platform.py (interactive mode)")
    
    else:
        # Interactive mode
        manager.run_interactive()

if __name__ == "__main__":
    main()