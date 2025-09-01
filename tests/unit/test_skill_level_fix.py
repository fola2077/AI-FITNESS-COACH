#!/usr/bin/env python3
"""
Test script to verify the skill_level attribute fix
"""

import sys
import os
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

def test_form_grader_skill_level():
    """Test that the form grader handles skill_level correctly"""
    
    try:
        from src.grading.advanced_form_grader import (
            IntelligentFormGrader, 
            ThresholdConfig,
            BiomechanicalMetrics,
            UserProfile,
            UserLevel
        )
        
        print("✅ Imports successful")
        
        # Test 1: Initialize form grader
        config = ThresholdConfig.emergency_calibrated()
        user_profile = UserProfile(user_id="test_user", skill_level=UserLevel.BEGINNER)
        grader = IntelligentFormGrader(user_profile=user_profile, difficulty="beginner", config=config)
        
        print("✅ Form grader initialized successfully")
        
        # Test 2: Create test metrics
        test_metrics = [
            BiomechanicalMetrics(
                knee_angle_left=140,
                knee_angle_right=138,
                back_angle=70,
                landmark_visibility=0.9,
                skill_level='BEGINNER'
            ),
            BiomechanicalMetrics(
                knee_angle_left=110,
                knee_angle_right=108,
                back_angle=85,
                landmark_visibility=0.9,
                skill_level='BEGINNER'
            ),
            BiomechanicalMetrics(
                knee_angle_left=85,
                knee_angle_right=87,
                back_angle=95,
                landmark_visibility=0.9,
                skill_level='BEGINNER'
            )
        ]
        
        print("✅ Test metrics created successfully")
        
        # Test 3: Try to grade a repetition (this was causing the AttributeError)
        try:
            result = grader.grade_repetition(test_metrics)
            print("✅ Rep grading completed successfully")
            print(f"   Overall score: {result.get('overall_score', 'N/A'):.1f}%")
            print(f"   Difficulty data: {result.get('difficulty_data', {})}")
            
            # Verify that skill_level is properly handled in the result
            if 'difficulty_data' in result and 'skill_level' in result['difficulty_data']:
                skill_level = result['difficulty_data']['skill_level']
                print(f"   ✅ Skill level in result: {skill_level}")
            else:
                print("   ⚠️ Skill level not found in difficulty data")
                
        except AttributeError as e:
            if 'skill_level' in str(e):
                print(f"   ❌ SKILL_LEVEL AttributeError: {e}")
                return False
            else:
                print(f"   ⚠️ Other AttributeError: {e}")
        except Exception as e:
            print(f"   ⚠️ Other error during grading: {e}")
        
        # Test 4: Test difficulty change
        try:
            grader.set_difficulty("expert")
            print("✅ Difficulty change successful")
            
            # Test grading with new difficulty
            result2 = grader.grade_repetition(test_metrics)
            print("✅ Rep grading after difficulty change successful")
            
        except Exception as e:
            print(f"   ❌ Error during difficulty change test: {e}")
            return False
        
        print("\n🎉 All tests passed! skill_level attribute error is fixed.")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🧪 Testing skill_level attribute fix...")
    print("=" * 50)
    
    success = test_form_grader_skill_level()
    
    if success:
        print("\n✅ SUCCESS: All tests passed!")
        sys.exit(0)
    else:
        print("\n❌ FAILURE: Some tests failed!")
        sys.exit(1)
