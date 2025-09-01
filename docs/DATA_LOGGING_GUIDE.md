# AI Fitness Coach - Data Logging System

## Overview

The AI Fitness Coach now includes a comprehensive data logging system designed to capture all metrics and user interactions in CSV spreadsheet format for analysis, evaluation, and ML model training.

## Quick Start

### Basic Usage

```python
from data.session_logger import DataLogger, LoggingConfig
from data.export_utils import DataExporter

# Configure logging
config = LoggingConfig(
    base_output_dir="data/logs",
    max_days_retention=90,
    quality_threshold=0.7
)

# Initialize logger
logger = DataLogger(config)

# Start session
session_id = logger.start_session("user_001", "SQUAT", {"skill_level": "INTERMEDIATE"})

# Log rep data
rep_id = logger.log_rep_start(1)
logger.log_frame_data(biomech_metrics, frame_number=1, movement_phase="DESCENDING")
logger.log_rep_completion({"final_form_score": 85}, {"notes": "Good rep"})

# End session
logger.end_session({"notes": "Session completed"})
```

### Data Export

```python
# Initialize exporter
exporter = DataExporter("data/logs")

# Export ML training dataset
ml_data = exporter.export_ml_training_dataset(
    output_file="ml_dataset.csv",
    filters={'min_form_score': 70}
)

# Generate user progress report
progress = exporter.export_user_progress_summary("user_001", "progress.txt")

# Export session analytics
analytics = exporter.export_session_analytics("analytics_output/")
```

## Data Structure

### 1. Session Data (`sessions/`)
High-level session summaries for user progress tracking:
- Session ID, user ID, timestamps
- Total reps, duration, average scores
- Session quality metrics
- Fatigue detection, improvement scores

### 2. Rep Data (`reps/`)
Individual repetition performance metrics:
- Rep ID, number, start/end times
- Form scores, depth achieved, faults
- Movement quality metrics
- Technical complexity assessments

### 3. Biomechanical Data (`biomechanics/`)
Frame-by-frame movement analysis:
- Joint angles (knees, hips, ankles)
- Center of mass, velocity, acceleration
- Symmetry ratios, stability metrics
- Frame quality and landmark visibility

### 4. ML Training Data (`ml_training/`)
Comprehensive feature sets for model training:
- 42+ engineered features
- Binary and categorical labels
- Movement phase classifications
- Context and sequence features

## Configuration Options

### LoggingConfig Parameters

```python
@dataclass
class LoggingConfig:
    base_output_dir: str = "data/logs"          # Output directory
    max_days_retention: int = 90                # Data retention period
    auto_cleanup: bool = True                   # Automatic cleanup
    quality_threshold: float = 0.7              # Quality threshold
    min_frames_per_rep: int = 10               # Minimum frames per rep
    include_raw_landmarks: bool = True          # Include raw pose data
    normalize_coordinates: bool = True          # Normalize coordinates
```

### Export Filters

```python
filters = {
    'min_form_score': 70,                      # Minimum form score
    'max_form_score': 100,                     # Maximum form score
    'min_frame_quality': 0.8,                 # Minimum frame quality
    'exclude_outliers': True,                  # Remove outliers
    'date_range': (start_date, end_date)       # Date range filter
}
```

## Data Quality Validation

### Automatic Checks
- **Directory Structure**: Validates all required directories exist
- **File Consistency**: Validates CSV headers and schema compliance
- **Data Quality**: Validates data ranges, types, and logical consistency
- **Cross-References**: Validates data relationships across file types

### Quality Scoring
- Overall quality score (0-100)
- Per-data-type quality assessment
- Issue identification and recommendations
- Automatic data cleaning suggestions

## Export Capabilities

### 1. ML Training Dataset Export
```python
# Export clean, filtered dataset for ML training
ml_export = exporter.export_ml_training_dataset(
    output_file="training_data.csv",
    filters={
        'min_form_score': 75,
        'min_frame_quality': 0.9,
        'exclude_outliers': True
    }
)
```

### 2. User Progress Analytics
```python
# Generate individual user progress report
progress = exporter.export_user_progress_summary(
    user_id="user_001",
    output_file="user_progress.txt"
)
```

### 3. Session Analytics
```python
# Export comprehensive analytics across all users
analytics = exporter.export_session_analytics("analytics_output/")
# Creates: user_analytics.csv, temporal_analytics.csv, 
#         performance_analytics.csv, fault_analytics.csv
```

## Integration with Main Application

### Pose Processing Integration
```python
# In your pose processing loop
logger.log_frame_data(
    biomech_metrics,
    analysis_results=analysis_data,
    frame_number=frame_count,
    movement_phase=current_phase
)
```

### Form Grader Integration
```python
# After rep analysis
logger.log_rep_completion(
    form_analysis={
        'final_form_score': grader.final_score,
        'faults_detected': len(grader.detected_faults),
        'fault_categories': ','.join(grader.fault_types)
    },
    feedback_data={
        'voice_feedback_given': voice_engine.is_enabled(),
        'feedback_type': feedback_manager.last_feedback_type
    }
)
```

## File Structure

```
data/logs/
├── sessions/
│   └── session_YYYYMM.csv          # Session-level data
├── reps/
│   └── rep_data_YYYYMM.csv         # Rep-level data
├── biomechanics/
│   └── biomech_YYYYMM.csv          # Frame-level data
└── ml_training/
    └── ml_dataset_YYYYMM.csv       # ML-ready features

exports/
├── ml_dataset_export.csv           # Filtered ML dataset
├── user_progress_reports/          # Individual progress reports
└── analytics/                     # Session analytics
    ├── user_analytics.csv
    ├── temporal_analytics.csv
    ├── performance_analytics.csv
    └── fault_analytics.csv
```

## Testing & Validation

### Run Tests
```bash
python test_data_logging.py        # Comprehensive test suite
python demo_data_logging.py        # Real-world demonstration
```

### Expected Output
- ✅ Session, rep, and frame data logged correctly
- ✅ Data integrity validation passes (100% score)
- ✅ ML dataset export with 42+ features
- ✅ Quality assessment scores 90%+

## Common Use Cases

### 1. ML Model Training
```python
# Export clean training data
exporter.export_ml_training_dataset(
    "training_data.csv",
    filters={'min_form_score': 80, 'min_frame_quality': 0.9}
)

# Features ready for:
# - Binary classification (good/bad rep)
# - Fault detection models
# - Form score regression
# - Movement phase classification
```

### 2. User Progress Tracking
```python
# Individual progress analysis
progress = exporter.export_user_progress_summary("user_001")
print(f"Average score: {progress['avg_form_score']}")
print(f"Improvement: {progress['improvement_points']} points")
print(f"Consistency: {progress['consistency_score']}")
```

### 3. Research & Analytics
```python
# Export comprehensive analytics
analytics = exporter.export_session_analytics()

# Analyze:
# - User performance trends
# - Common fault patterns
# - Coaching effectiveness
# - System usage patterns
```

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure `src/` is in Python path
2. **Permission Errors**: Check write permissions for output directory
3. **Missing Data**: Verify all required biomechanical metrics are provided
4. **Quality Issues**: Check frame quality and landmark visibility

### Debugging
```python
# Validate data integrity
validation = logger.validate_data_integrity()
print(f"Overall status: {validation['overall_status']}")

# Check quality scores
quality = exporter.validate_data_quality()
print(f"Quality score: {quality['overall_quality_score']}")
```

## Performance Considerations

- **Real-time Impact**: Minimal impact on pose processing (< 1ms per frame)
- **Memory Usage**: Efficient buffering prevents memory overflow
- **Disk Space**: Automatic cleanup based on retention policies
- **File Sizes**: Optimized CSV formatting for manageable file sizes

## Next Steps

1. **Integration**: Integrate into main application pipeline
2. **ML Training**: Use exported data to train lightweight models
3. **Analytics**: Set up automated reporting and dashboards
4. **Research**: Publish findings using comprehensive dataset

For detailed implementation examples, see:
- `test_data_logging.py` - Comprehensive test suite
- `demo_data_logging.py` - Real-world usage demonstration
- `src/data/session_logger.py` - Core implementation
- `src/data/export_utils.py` - Export and analytics utilities
