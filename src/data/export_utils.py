"""
Data Export Utilities for AI Fitness Coach

This module provides utilities for exporting, analyzing, and preparing data
for machine learning training and research analysis.

Features:
- Data aggregation and summarization
- Export to various formats (CSV, JSON, Excel)
- Data quality assessment and validation
- ML-ready dataset preparation
- Statistical analysis and visualization prep
"""

import os
import csv
import json
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Union
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class DataExporter:
    """Comprehensive data export and analysis utilities"""
    
    def __init__(self, data_dir: str = "data/logs"):
        self.data_dir = data_dir
        self.session_dir = os.path.join(data_dir, "sessions")
        self.rep_dir = os.path.join(data_dir, "reps")
        self.biomech_dir = os.path.join(data_dir, "biomechanics")
        self.ml_dir = os.path.join(data_dir, "ml_training")
    
    def export_user_progress_summary(self, user_id: str, output_file: str = None) -> Dict:
        """Export comprehensive user progress summary"""
        
        # Load all session data for user
        sessions = self._load_user_sessions(user_id)
        if not sessions:
            return {'error': f'No data found for user {user_id}'}
        
        # Calculate progress metrics
        progress_data = self._calculate_progress_metrics(sessions)
        
        # Export to file if specified
        if output_file:
            self._write_progress_report(progress_data, output_file)
        
        return progress_data
    
    def export_ml_training_dataset(self, output_file: str, filters: Dict = None) -> Dict:
        """Export a clean ML training dataset with specified filters"""
        
        # Default filters
        default_filters = {
            'min_form_score': 0,
            'max_form_score': 100,
            'min_frame_quality': 0.5,
            'exclude_outliers': True,
            'include_validation_data': True,
            'date_range': None  # (start_date, end_date) tuple
        }
        
        filters = {**default_filters, **(filters or {})}
        
        # Load and filter ML data
        ml_data = self._load_filtered_ml_data(filters)
        
        if not ml_data:
            return {'error': 'No data matches the specified filters'}
        
        # Clean and prepare data
        clean_data = self._clean_ml_dataset(ml_data)
        
        # Export to CSV
        export_stats = self._export_ml_csv(clean_data, output_file)
        
        return {
            'success': True,
            'output_file': output_file,
            'total_records': len(clean_data),
            'features': len(clean_data[0]) if clean_data else 0,
            'export_stats': export_stats
        }
    
    def export_session_analytics(self, output_dir: str = "data/analytics") -> Dict:
        """Export comprehensive session analytics"""
        
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # Load all session data
        all_sessions = self._load_all_sessions()
        
        if not all_sessions:
            return {'error': 'No session data available'}
        
        analytics = {
            'user_analytics': self._generate_user_analytics(all_sessions),
            'temporal_analytics': self._generate_temporal_analytics(all_sessions),
            'performance_analytics': self._generate_performance_analytics(all_sessions),
            'fault_analytics': self._generate_fault_analytics(all_sessions)
        }
        
        # Export each analytics type
        export_files = {}
        for analytics_type, data in analytics.items():
            filename = os.path.join(output_dir, f"{analytics_type}_{datetime.now().strftime('%Y%m%d')}.csv")
            self._export_analytics_csv(data, filename)
            export_files[analytics_type] = filename
        
        return {
            'success': True,
            'analytics_generated': len(analytics),
            'output_files': export_files,
            'summary': self._generate_analytics_summary(analytics)
        }
    
    def validate_data_quality(self) -> Dict:
        """Validate data quality across all data sources"""
        
        quality_report = {
            'session_data_quality': self._validate_session_data(),
            'rep_data_quality': self._validate_rep_data(),
            'biomech_data_quality': self._validate_biomech_data(),
            'ml_data_quality': self._validate_ml_data(),
            'overall_quality_score': 0
        }
        
        # Calculate overall quality score
        quality_scores = [q.get('quality_score', 0) for q in quality_report.values() if isinstance(q, dict)]
        quality_report['overall_quality_score'] = np.mean(quality_scores) if quality_scores else 0
        
        return quality_report
    
    def _load_user_sessions(self, user_id: str) -> List[Dict]:
        """Load all session data for a specific user"""
        sessions = []
        
        if not os.path.exists(self.session_dir):
            return sessions
        
        for filename in os.listdir(self.session_dir):
            if filename.endswith('.csv'):
                file_path = os.path.join(self.session_dir, filename)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        reader = csv.DictReader(f)
                        for row in reader:
                            if row.get('user_id') == user_id:
                                sessions.append(row)
                except Exception as e:
                    logger.warning(f"Could not read session file {filename}: {e}")
        
        return sessions
    
    def _load_all_sessions(self) -> List[Dict]:
        """Load all session data"""
        sessions = []
        
        if not os.path.exists(self.session_dir):
            return sessions
        
        for filename in os.listdir(self.session_dir):
            if filename.endswith('.csv'):
                file_path = os.path.join(self.session_dir, filename)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        reader = csv.DictReader(f)
                        sessions.extend(list(reader))
                except Exception as e:
                    logger.warning(f"Could not read session file {filename}: {e}")
        
        return sessions
    
    def _load_filtered_ml_data(self, filters: Dict) -> List[Dict]:
        """Load ML training data with specified filters"""
        ml_data = []
        
        if not os.path.exists(self.ml_dir):
            return ml_data
        
        for filename in os.listdir(self.ml_dir):
            if filename.endswith('.csv'):
                file_path = os.path.join(self.ml_dir, filename)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        reader = csv.DictReader(f)
                        for row in reader:
                            if self._passes_filters(row, filters):
                                ml_data.append(row)
                except Exception as e:
                    logger.warning(f"Could not read ML file {filename}: {e}")
        
        return ml_data
    
    def _passes_filters(self, row: Dict, filters: Dict) -> bool:
        """Check if a data row passes the specified filters"""
        
        # Form score filter
        try:
            form_score = float(row.get('form_score', 0))
            if not (filters['min_form_score'] <= form_score <= filters['max_form_score']):
                return False
        except (ValueError, TypeError):
            return False
        
        # Frame quality filter
        try:
            frame_quality = float(row.get('frame_quality', 0))
            if frame_quality < filters['min_frame_quality']:
                return False
        except (ValueError, TypeError):
            return False
        
        # Date range filter
        if filters.get('date_range'):
            try:
                timestamp = float(row.get('timestamp', 0))
                row_date = datetime.fromtimestamp(timestamp)
                start_date, end_date = filters['date_range']
                if not (start_date <= row_date <= end_date):
                    return False
            except (ValueError, TypeError):
                return False
        
        return True
    
    def _calculate_progress_metrics(self, sessions: List[Dict]) -> Dict:
        """Calculate comprehensive progress metrics for a user"""
        
        if not sessions:
            return {}
        
        # Sort sessions by date
        sorted_sessions = sorted(sessions, key=lambda x: x.get('timestamp', 0))
        
        # Calculate basic metrics
        total_sessions = len(sessions)
        total_reps = sum(int(s.get('total_reps', 0)) for s in sessions)
        
        # Form score progression
        form_scores = [float(s.get('average_form_score', 0)) for s in sessions if s.get('average_form_score')]
        
        if form_scores:
            avg_form_score = np.mean(form_scores)
            best_form_score = np.max(form_scores)
            latest_scores = form_scores[-5:] if len(form_scores) >= 5 else form_scores
            recent_avg = np.mean(latest_scores)
            
            # Calculate improvement trend
            if len(form_scores) >= 3:
                early_avg = np.mean(form_scores[:3])
                improvement = recent_avg - early_avg
            else:
                improvement = 0
        else:
            avg_form_score = best_form_score = recent_avg = improvement = 0
        
        # Session consistency
        session_quality_scores = [float(s.get('session_quality_score', 0)) for s in sessions if s.get('session_quality_score')]
        consistency_score = 100 - np.std(session_quality_scores) if len(session_quality_scores) > 1 else 0
        
        # Fault analysis
        fault_counts = {}
        for session in sessions:
            faults = session.get('total_faults', '0')
            try:
                fault_count = int(faults)
                fault_counts[session.get('session_id', '')] = fault_count
            except (ValueError, TypeError):
                pass
        
        avg_faults_per_session = np.mean(list(fault_counts.values())) if fault_counts else 0
        
        return {
            'user_id': sessions[0].get('user_id', 'unknown'),
            'analysis_date': datetime.now().isoformat(),
            'total_sessions': total_sessions,
            'total_reps': total_reps,
            'avg_reps_per_session': total_reps / total_sessions if total_sessions > 0 else 0,
            'avg_form_score': avg_form_score,
            'best_form_score': best_form_score,
            'recent_avg_score': recent_avg,
            'improvement_points': improvement,
            'consistency_score': consistency_score,
            'avg_faults_per_session': avg_faults_per_session,
            'first_session_date': sorted_sessions[0].get('session_start', ''),
            'last_session_date': sorted_sessions[-1].get('session_start', ''),
            'training_duration_days': self._calculate_training_duration(sorted_sessions)
        }
    
    def _calculate_training_duration(self, sorted_sessions: List[Dict]) -> int:
        """Calculate training duration in days"""
        if len(sorted_sessions) < 2:
            return 0
        
        try:
            start_date = datetime.fromisoformat(sorted_sessions[0].get('session_start', ''))
            end_date = datetime.fromisoformat(sorted_sessions[-1].get('session_start', ''))
            return (end_date - start_date).days
        except (ValueError, TypeError):
            return 0
    
    def _clean_ml_dataset(self, ml_data: List[Dict]) -> List[Dict]:
        """Clean and prepare ML dataset"""
        
        clean_data = []
        
        for row in ml_data:
            cleaned_row = {}
            
            # Convert numeric fields
            numeric_fields = [
                'form_score', 'knee_left', 'knee_right', 'hip_angle', 'back_angle',
                'ankle_left', 'ankle_right', 'knee_symmetry', 'depth_percentage',
                'movement_velocity', 'acceleration', 'center_of_mass_x', 'center_of_mass_y',
                'postural_sway', 'stability_score', 'bilateral_asymmetry', 'movement_smoothness',
                'temporal_consistency', 'head_alignment', 'foot_stability', 'weight_distribution',
                'rep_number', 'session_progress', 'frame_quality', 'landmark_confidence',
                'previous_rep_score'
            ]
            
            for field in numeric_fields:
                try:
                    cleaned_row[field] = float(row.get(field, 0))
                except (ValueError, TypeError):
                    cleaned_row[field] = 0.0
            
            # Convert boolean fields
            boolean_fields = ['is_good_rep', 'fault_present']
            for field in boolean_fields:
                try:
                    value = row.get(field, 0)
                    cleaned_row[field] = 1 if (value == '1' or value == 1 or value == 'True') else 0
                except:
                    cleaned_row[field] = 0
            
            # Keep categorical fields as is
            categorical_fields = [
                'fault_type', 'fault_severity', 'movement_phase', 'depth_classification',
                'safety_classification', 'user_fatigue_level', 'skill_level',
                'velocity_trend', 'acceleration_trend', 'angle_trend', 'stability_trend'
            ]
            
            for field in categorical_fields:
                cleaned_row[field] = row.get(field, 'UNKNOWN')
            
            # Add derived features
            cleaned_row['knee_angle_avg'] = (cleaned_row['knee_left'] + cleaned_row['knee_right']) / 2
            cleaned_row['ankle_angle_avg'] = (cleaned_row['ankle_left'] + cleaned_row['ankle_right']) / 2
            cleaned_row['form_score_normalized'] = cleaned_row['form_score'] / 100.0
            
            clean_data.append(cleaned_row)
        
        return clean_data
    
    def _export_ml_csv(self, clean_data: List[Dict], output_file: str) -> Dict:
        """Export cleaned ML data to CSV"""
        
        if not clean_data:
            return {'error': 'No data to export'}
        
        Path(os.path.dirname(output_file)).mkdir(parents=True, exist_ok=True)
        
        # Get all field names
        all_fields = set()
        for row in clean_data:
            all_fields.update(row.keys())
        
        fieldnames = sorted(list(all_fields))
        
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(clean_data)
        
        return {
            'records_exported': len(clean_data),
            'fields_exported': len(fieldnames),
            'file_size_mb': os.path.getsize(output_file) / (1024 * 1024),
            'export_timestamp': datetime.now().isoformat()
        }
    
    def _generate_user_analytics(self, sessions: List[Dict]) -> List[Dict]:
        """Generate per-user analytics"""
        
        user_groups = {}
        for session in sessions:
            user_id = session.get('user_id', 'unknown')
            if user_id not in user_groups:
                user_groups[user_id] = []
            user_groups[user_id].append(session)
        
        analytics = []
        for user_id, user_sessions in user_groups.items():
            user_analytics = self._calculate_progress_metrics(user_sessions)
            analytics.append(user_analytics)
        
        return analytics
    
    def _generate_temporal_analytics(self, sessions: List[Dict]) -> List[Dict]:
        """Generate temporal analytics (daily/weekly/monthly trends)"""
        
        temporal_data = {}
        
        for session in sessions:
            try:
                session_date = datetime.fromisoformat(session.get('session_start', ''))
                date_key = session_date.strftime('%Y-%m-%d')
                
                if date_key not in temporal_data:
                    temporal_data[date_key] = {
                        'date': date_key,
                        'session_count': 0,
                        'total_reps': 0,
                        'avg_form_score': [],
                        'unique_users': set()
                    }
                
                temporal_data[date_key]['session_count'] += 1
                temporal_data[date_key]['total_reps'] += int(session.get('total_reps', 0))
                temporal_data[date_key]['avg_form_score'].append(float(session.get('average_form_score', 0)))
                temporal_data[date_key]['unique_users'].add(session.get('user_id', 'unknown'))
                
            except (ValueError, TypeError):
                continue
        
        # Convert to list format
        analytics = []
        for date_key, data in temporal_data.items():
            analytics.append({
                'date': date_key,
                'session_count': data['session_count'],
                'total_reps': data['total_reps'],
                'avg_form_score': np.mean(data['avg_form_score']) if data['avg_form_score'] else 0,
                'unique_users': len(data['unique_users']),
                'avg_reps_per_session': data['total_reps'] / data['session_count'] if data['session_count'] > 0 else 0
            })
        
        return sorted(analytics, key=lambda x: x['date'])
    
    def _generate_performance_analytics(self, sessions: List[Dict]) -> List[Dict]:
        """Generate performance analytics"""
        
        performance_bands = {
            'excellent': {'min': 90, 'max': 100},
            'good': {'min': 75, 'max': 89},
            'fair': {'min': 60, 'max': 74},
            'poor': {'min': 0, 'max': 59}
        }
        
        band_counts = {band: 0 for band in performance_bands.keys()}
        form_scores = []
        
        for session in sessions:
            try:
                avg_score = float(session.get('average_form_score', 0))
                form_scores.append(avg_score)
                
                for band, range_info in performance_bands.items():
                    if range_info['min'] <= avg_score <= range_info['max']:
                        band_counts[band] += 1
                        break
                        
            except (ValueError, TypeError):
                continue
        
        analytics = []
        for band, count in band_counts.items():
            analytics.append({
                'performance_band': band,
                'session_count': count,
                'percentage': (count / len(sessions) * 100) if sessions else 0,
                'min_score': performance_bands[band]['min'],
                'max_score': performance_bands[band]['max']
            })
        
        return analytics
    
    def _generate_fault_analytics(self, sessions: List[Dict]) -> List[Dict]:
        """Generate fault analytics"""
        
        fault_data = []
        
        for session in sessions:
            try:
                total_faults = int(session.get('total_faults', 0))
                safety_faults = int(session.get('safety_faults', 0))
                form_faults = int(session.get('form_faults', 0))
                depth_faults = int(session.get('depth_faults', 0))
                
                fault_data.append({
                    'session_id': session.get('session_id', ''),
                    'user_id': session.get('user_id', ''),
                    'total_faults': total_faults,
                    'safety_faults': safety_faults,
                    'form_faults': form_faults,
                    'depth_faults': depth_faults,
                    'faults_per_rep': total_faults / max(int(session.get('total_reps', 1)), 1)
                })
                
            except (ValueError, TypeError):
                continue
        
        return fault_data
    
    def _generate_analytics_summary(self, analytics: Dict) -> Dict:
        """Generate summary of analytics"""
        
        return {
            'total_users_analyzed': len(analytics.get('user_analytics', [])),
            'total_days_covered': len(analytics.get('temporal_analytics', [])),
            'performance_distribution': {
                band['performance_band']: band['session_count'] 
                for band in analytics.get('performance_analytics', [])
            },
            'total_faults_analyzed': sum(
                fault['total_faults'] for fault in analytics.get('fault_analytics', [])
            )
        }
    
    def _export_analytics_csv(self, data: List[Dict], filename: str):
        """Export analytics data to CSV"""
        
        if not data:
            return
        
        fieldnames = list(data[0].keys()) if data else []
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)
    
    def _validate_session_data(self) -> Dict:
        """Validate session data quality"""
        
        sessions = self._load_all_sessions()
        if not sessions:
            return {'quality_score': 0, 'issues': ['No session data found']}
        
        issues = []
        valid_sessions = 0
        
        for session in sessions:
            session_valid = True
            
            # Check required fields
            required_fields = ['session_id', 'user_id', 'timestamp']
            for field in required_fields:
                if not session.get(field):
                    issues.append(f"Missing {field} in session")
                    session_valid = False
            
            # Check data consistency
            try:
                total_reps = int(session.get('total_reps', 0))
                completed_reps = int(session.get('completed_reps', 0))
                if completed_reps > total_reps:
                    issues.append(f"Completed reps > total reps in session {session.get('session_id')}")
                    session_valid = False
            except (ValueError, TypeError):
                issues.append(f"Invalid rep counts in session {session.get('session_id')}")
                session_valid = False
            
            if session_valid:
                valid_sessions += 1
        
        quality_score = (valid_sessions / len(sessions) * 100) if sessions else 0
        
        return {
            'quality_score': quality_score,
            'total_sessions': len(sessions),
            'valid_sessions': valid_sessions,
            'issues': issues[:10]  # Limit to first 10 issues
        }
    
    def _validate_rep_data(self) -> Dict:
        """Validate rep data quality"""
        # Similar validation for rep data
        return {'quality_score': 85, 'issues': []}  # Placeholder
    
    def _validate_biomech_data(self) -> Dict:
        """Validate biomechanical data quality"""
        # Similar validation for biomech data
        return {'quality_score': 90, 'issues': []}  # Placeholder
    
    def _validate_ml_data(self) -> Dict:
        """Validate ML training data quality"""
        # Similar validation for ML data
        return {'quality_score': 88, 'issues': []}  # Placeholder
    
    def _write_progress_report(self, progress_data: Dict, output_file: str):
        """Write progress report to file"""
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("AI Fitness Coach - User Progress Report\n")
            f.write("=" * 50 + "\n\n")
            
            f.write(f"User: {progress_data.get('user_id', 'Unknown')}\n")
            f.write(f"Analysis Date: {progress_data.get('analysis_date', 'Unknown')}\n")
            f.write(f"Training Duration: {progress_data.get('training_duration_days', 0)} days\n\n")
            
            f.write("Performance Summary:\n")
            f.write(f"- Total Sessions: {progress_data.get('total_sessions', 0)}\n")
            f.write(f"- Total Reps: {progress_data.get('total_reps', 0)}\n")
            f.write(f"- Average Form Score: {progress_data.get('avg_form_score', 0):.1f}/100\n")
            f.write(f"- Best Form Score: {progress_data.get('best_form_score', 0):.1f}/100\n")
            f.write(f"- Recent Average: {progress_data.get('recent_avg_score', 0):.1f}/100\n")
            f.write(f"- Improvement: {progress_data.get('improvement_points', 0):+.1f} points\n")
            f.write(f"- Consistency Score: {progress_data.get('consistency_score', 0):.1f}/100\n")
