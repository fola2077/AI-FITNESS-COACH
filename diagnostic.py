#!/usr/bin/env python3
"""
AI Fitness Coach Diagnostic Script
Identifies import issues, missing files, and configuration problems
"""

import sys
import os
from pathlib import Path

def diagnose_imports():
    """Test all critical imports"""
    print("🔍 Testing Critical Imports...")
    issues = []
    
    critical_modules = [
        ('PySide6.QtWidgets', 'QApplication'),
        ('cv2', None),
        ('mediapipe', 'solutions'),
        ('numpy', None),
        ('pyttsx3', None),
    ]
    
    for module, attr in critical_modules:
        try:
            imported = __import__(module)
            if attr and not hasattr(imported, attr):
                issues.append(f"❌ {module}.{attr} not available")
            else:
                print(f"✅ {module} - OK")
        except ImportError as e:
            issues.append(f"❌ Cannot import {module}: {e}")
            print(f"❌ {module} - FAILED: {e}")
    
    return issues

def diagnose_project_structure():
    """Check if all expected files exist"""
    print("\n🏗️ Checking Project Structure...")
    expected_files = [
        'src/__init__.py',
        'src/gui/__init__.py',
        'src/gui/main_window.py',
        'src/processing/__init__.py',
        'src/processing/pose_processor.py',
        'src/feedback/__init__.py',
        'src/feedback/enhanced_feedback_manager.py',
        'src/grading/__init__.py',
        'src/grading/advanced_form_grader.py',
        'src/pose/__init__.py',
        'src/pose/pose_detector.py',
        'requirements.txt',
        'run_app.py'
    ]
    
    missing = []
    for file_path in expected_files:
        if Path(file_path).exists():
            print(f"✅ {file_path}")
        else:
            missing.append(file_path)
            print(f"❌ {file_path} - MISSING")
    
    return missing

def diagnose_project_imports():
    """Test project-specific imports"""
    print("\n🎯 Testing Project Imports...")
    issues = []
    
    # Add project root to path
    project_root = Path(__file__).parent.absolute()
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    
    project_modules = [
        ('src.gui.main_window', 'MainWindow'),
        ('src.processing.pose_processor', 'PoseProcessor'),
        ('src.feedback.enhanced_feedback_manager', 'EnhancedFeedbackManager'),
        ('src.grading.advanced_form_grader', 'IntelligentFormGrader'),
        ('src.pose.pose_detector', 'PoseDetector'),
    ]
    
    for module, class_name in project_modules:
        try:
            imported = __import__(module, fromlist=[class_name])
            if hasattr(imported, class_name):
                print(f"✅ {module}.{class_name}")
            else:
                issues.append(f"❌ {module}.{class_name} class not found")
                print(f"❌ {module}.{class_name} - CLASS NOT FOUND")
        except ImportError as e:
            issues.append(f"❌ Cannot import {module}: {e}")
            print(f"❌ {module} - IMPORT FAILED: {e}")
        except Exception as e:
            issues.append(f"❌ Error importing {module}: {e}")
            print(f"❌ {module} - ERROR: {e}")
    
    return issues

def test_enhanced_feedback_manager():
    """Test the specific method causing issues"""
    print("\n🎙️ Testing EnhancedFeedbackManager...")
    try:
        from src.feedback.enhanced_feedback_manager import EnhancedFeedbackManager
        
        # Create instance
        manager = EnhancedFeedbackManager()
        
        # Check if process_pose_analysis method exists
        if hasattr(manager, 'process_pose_analysis'):
            print("✅ process_pose_analysis method exists")
            
            # Check method signature
            import inspect
            sig = inspect.signature(manager.process_pose_analysis)
            params = list(sig.parameters.keys())
            print(f"📋 Method signature: {params}")
            
            # Test with minimal arguments
            try:
                result = manager.process_pose_analysis({})
                print("✅ process_pose_analysis accepts empty dict")
            except TypeError as e:
                print(f"❌ process_pose_analysis signature issue: {e}")
                return [f"Method signature issue: {e}"]
            except Exception as e:
                print(f"⚠️ process_pose_analysis runtime issue: {e}")
        else:
            print("❌ process_pose_analysis method not found")
            return ["process_pose_analysis method missing"]
        
        return []
        
    except Exception as e:
        print(f"❌ EnhancedFeedbackManager test failed: {e}")
        return [f"EnhancedFeedbackManager error: {e}"]

def check_python_environment():
    """Check Python version and virtual environment"""
    print("\n🐍 Python Environment Check...")
    
    print(f"Python Version: {sys.version}")
    print(f"Python Executable: {sys.executable}")
    
    # Check if in virtual environment
    in_venv = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
    print(f"Virtual Environment: {'✅ Active' if in_venv else '❌ Not detected'}")
    
    # Check site-packages
    import site
    print(f"Site Packages: {site.getsitepackages()}")
    
    return []

def check_configuration_files():
    """Check configuration and requirements files"""
    print("\n⚙️ Configuration Files Check...")
    issues = []
    
    config_files = [
        ('requirements.txt', 'Dependencies file'),
        ('pyproject.toml', 'Project configuration'),
        ('.gitignore', 'Git ignore file'),
    ]
    
    for file_path, description in config_files:
        if Path(file_path).exists():
            print(f"✅ {file_path} - {description}")
            
            # Check requirements.txt content
            if file_path == 'requirements.txt':
                try:
                    with open(file_path, 'r') as f:
                        reqs = f.read().strip()
                        if reqs:
                            print(f"   📦 {len(reqs.splitlines())} dependencies listed")
                        else:
                            issues.append("requirements.txt is empty")
                            print("   ⚠️ File is empty")
                except Exception as e:
                    issues.append(f"Cannot read requirements.txt: {e}")
        else:
            print(f"⚠️ {file_path} - {description} (optional)")
    
    return issues

def main():
    """Run all diagnostic tests"""
    print("🔍 AI Fitness Coach Comprehensive Diagnostic")
    print("=" * 60)
    
    all_issues = []
    
    # Test 1: Python Environment
    env_issues = check_python_environment()
    all_issues.extend(env_issues)
    
    # Test 2: Configuration Files
    config_issues = check_configuration_files()
    all_issues.extend(config_issues)
    
    # Test 3: Critical Imports
    import_issues = diagnose_imports()
    all_issues.extend(import_issues)
    
    # Test 4: Project Structure
    missing_files = diagnose_project_structure()
    if missing_files:
        all_issues.extend([f"Missing file: {f}" for f in missing_files])
    
    # Test 5: Project Imports
    project_issues = diagnose_project_imports()
    all_issues.extend(project_issues)
    
    # Test 6: Enhanced Feedback Manager
    feedback_issues = test_enhanced_feedback_manager()
    all_issues.extend(feedback_issues)
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 DIAGNOSTIC SUMMARY")
    print("=" * 60)
    
    if all_issues:
        print(f"❌ Found {len(all_issues)} issues:")
        for i, issue in enumerate(all_issues, 1):
            print(f"  {i}. {issue}")
        
        print("\n🔧 Recommended Actions:")
        if any("Cannot import" in issue for issue in all_issues):
            print("  • Install missing dependencies: pip install -r requirements.txt")
        if any("Missing file" in issue for issue in all_issues):
            print("  • Check if files were moved or renamed")
        if any("signature issue" in issue for issue in all_issues):
            print("  • Fix method signatures in EnhancedFeedbackManager")
        
    else:
        print("🎉 No critical issues detected!")
        print("Your AI Fitness Coach project appears to be properly configured.")
    
    return len(all_issues) == 0

if __name__ == '__main__':
    success = main()
    
    print(f"\n{'='*60}")
    if success:
        print("✅ Diagnostic completed successfully!")
    else:
        print("❌ Issues found - see recommendations above")
    
    print("Press Enter to continue...")
    try:
        input()
    except:
        pass
    
    sys.exit(0 if success else 1)
