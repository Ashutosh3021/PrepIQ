import logging
from typing import Dict, Any, List
from datetime import datetime, timedelta
import random
from sqlalchemy.orm import Session
from .. import models
import json

logger = logging.getLogger(__name__)

class StudyPlanner:
    """
    AI-powered study schedule optimization with dynamic adjustment based on progress,
    spaced repetition algorithms, and personalized topic sequencing.
    """
    
    def __init__(self):
        # Spaced repetition intervals (in days)
        self.spaced_repetition_intervals = [1, 3, 7, 14, 30, 60]
        
        # Difficulty weights for topics
        self.difficulty_weights = {
            'beginner': 0.5,
            'intermediate': 1.0,
            'advanced': 1.5
        }
        
        # Priority weights for different topic types
        self.priority_weights = {
            'high': 2.0,
            'medium': 1.0,
            'low': 0.5
        }
    
    def generate_optimized_study_plan(self, 
                                    subject_id: str, 
                                    user_id: str, 
                                    start_date: str, 
                                    exam_date: str, 
                                    db: Session,
                                    user_performance: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Generate an AI-optimized study plan based on subject content, user performance,
        and learning science principles
        """
        # Get subject information
        subject = db.query(models.Subject).filter(
            models.Subject.id == subject_id,
            models.Subject.user_id == user_id
        ).first()
        
        if not subject:
            raise ValueError("Subject not found or doesn't belong to user")
        
        # Parse dates
        start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00')) if 'Z' in start_date else datetime.fromisoformat(start_date)
        exam_dt = datetime.fromisoformat(exam_date.replace('Z', '+00:00')) if 'Z' in exam_date else datetime.fromisoformat(exam_date)
        
        # Calculate total days
        total_days = (exam_dt - start_dt).days + 1
        
        # Get subject syllabus and topics
        syllabus = subject.syllabus_json or {"units": []}
        
        # Get historical question data for topic importance analysis
        historical_questions = db.query(models.Question).join(
            models.QuestionPaper
        ).filter(
            models.QuestionPaper.subject_id == subject_id
        ).all()
        
        # Analyze topic importance from historical data
        topic_importance = self._analyze_topic_importance(historical_questions)
        
        # Get user's weak areas if available
        weak_areas = []
        strong_areas = []
        if user_performance:
            weak_areas = user_performance.get('weak_topics', [])
            strong_areas = user_performance.get('strong_topics', [])
        
        # Generate daily schedule
        daily_schedule = self._generate_daily_schedule(
            syllabus, 
            topic_importance, 
            weak_areas, 
            strong_areas, 
            total_days, 
            start_dt
        )
        
        return {
            "plan_id": f"study_plan_{subject_id}_{user_id}_{datetime.now().strftime('%Y%m%d')}",
            "subject_id": subject_id,
            "subject_name": subject.name,
            "start_date": start_date,
            "exam_date": exam_date,
            "total_days": total_days,
            "daily_schedule": daily_schedule,
            "optimization_strategy": "AI-powered with spaced repetition and personalized focus",
            "generated_at": datetime.now().isoformat()
        }
    
    def _analyze_topic_importance(self, questions: List[Any]) -> Dict[str, float]:
        """
        Analyze topic importance based on historical question frequency and marks distribution
        """
        topic_importance = {}
        
        for q in questions:
            unit_name = getattr(q, 'unit_name', 'Unknown')
            marks = getattr(q, 'marks', 5)
            
            if unit_name not in topic_importance:
                topic_importance[unit_name] = {'frequency': 0, 'total_marks': 0}
            
            topic_importance[unit_name]['frequency'] += 1
            topic_importance[unit_name]['total_marks'] += marks
        
        # Normalize importance scores
        max_freq = max([data['frequency'] for data in topic_importance.values()], default=1)
        max_marks = max([data['total_marks'] for data in topic_importance.values()], default=1)
        
        normalized_importance = {}
        for topic, data in topic_importance.items():
            # Combine frequency and marks for importance score
            freq_score = data['frequency'] / max_freq
            marks_score = data['total_marks'] / max_marks
            normalized_importance[topic] = (freq_score * 0.6) + (marks_score * 0.4)  # Weighted combination
        
        return normalized_importance
    
    def _generate_daily_schedule(self, 
                               syllabus: Dict[str, Any], 
                               topic_importance: Dict[str, float], 
                               weak_areas: List[str], 
                               strong_areas: List[str], 
                               total_days: int, 
                               start_date: datetime) -> List[Dict[str, Any]]:
        """
        Generate daily study schedule with AI-optimized topic distribution
        """
        # Extract all topics from syllabus
        all_topics = []
        unit_topic_mapping = {}
        
        for unit in syllabus.get('units', []):
            unit_name = unit.get('name', 'Unknown Unit')
            for topic in unit.get('topics', []):
                all_topics.append({
                    'name': topic,
                    'unit': unit_name,
                    'importance': topic_importance.get(topic, 0.5),
                    'is_weak_area': topic in weak_areas,
                    'is_strong_area': topic in strong_areas
                })
                if unit_name not in unit_topic_mapping:
                    unit_topic_mapping[unit_name] = []
                unit_topic_mapping[unit_name].append(topic)
        
        if not all_topics:
            # Fallback if no topics found in syllabus
            all_topics = [
                {
                    'name': f'Topic {i+1}', 
                    'unit': f'Unit {(i//3)+1}', 
                    'importance': 0.5, 
                    'is_weak_area': False, 
                    'is_strong_area': False
                } 
                for i in range(12)  # Create 12 default topics
            ]
        
        # Sort topics by importance (descending) and whether they're weak areas
        sorted_topics = sorted(all_topics, 
                              key=lambda x: (x['importance'] * (1.5 if x['is_weak_area'] else 1.0)), 
                              reverse=True)
        
        # Distribute topics across days
        daily_schedule = []
        current_date = start_date
        
        # Calculate topics per day based on total topics and days
        topics_per_day = max(1, len(sorted_topics) // total_days)
        
        topic_idx = 0
        for day in range(1, total_days + 1):
            day_topics = []
            
            # Assign topics for this day
            topics_for_day = min(topics_per_day, len(sorted_topics) - topic_idx)
            
            # Adjust assignment based on topic importance and weak areas
            if topic_idx < len(sorted_topics):
                # Prioritize weak areas and high-importance topics
                remaining_topics = sorted_topics[topic_idx:]
                
                # Select topics for today considering importance and weaknesses
                selected_indices = self._select_topics_for_day(remaining_topics, topics_for_day)
                
                for idx in selected_indices:
                    if topic_idx + idx < len(sorted_topics):
                        topic = sorted_topics[topic_idx + idx]
                        day_topics.append({
                            'name': topic['name'],
                            'unit': topic['unit'],
                            'importance': topic['importance'],
                            'is_weak_area': topic['is_weak_area'],
                            'study_duration_hours': self._calculate_study_duration(topic)
                        })
                
                # Move index forward by the number of topics assigned
                topic_idx += len(selected_indices)
            
            # Add review sessions for previously studied topics
            if day > 1:
                review_topics = self._select_review_topics(daily_schedule, day)
                day_topics.extend(review_topics)
            
            daily_schedule.append({
                "day": day,
                "date": current_date.strftime("%Y-%m-%d"),
                "topics": day_topics,
                "recommended_hours": sum([t.get('study_duration_hours', 1) for t in day_topics]),
                "focus_topics": [t['name'] for t in day_topics if t.get('is_weak_area')],
                "spaced_repetition_session": len([t for t in day_topics if t.get('is_review', False)]) > 0
            })
            
            current_date += timedelta(days=1)
        
        return daily_schedule
    
    def _select_topics_for_day(self, remaining_topics: List[Dict], max_topics: int) -> List[int]:
        """
        Select topics for the current day based on importance and weaknesses
        """
        if not remaining_topics or max_topics <= 0:
            return []
        
        # Prioritize weak areas first, then high importance topics
        priority_indices = []
        
        # Find weak areas in remaining topics
        weak_area_indices = [i for i, topic in enumerate(remaining_topics) if topic['is_weak_area']]
        
        # Find high importance topics
        high_importance_indices = [i for i, topic in enumerate(remaining_topics) 
                                  if not remaining_topics[i]['is_weak_area'] and 
                                  remaining_topics[i]['importance'] > 0.7]
        
        # Find medium importance topics
        medium_importance_indices = [i for i, topic in enumerate(remaining_topics) 
                                    if not remaining_topics[i]['is_weak_area'] and 
                                    0.4 <= remaining_topics[i]['importance'] <= 0.7]
        
        # Select topics based on priority
        selected = []
        
        # Add weak areas (maximum 2 per day)
        weak_to_add = min(2, len(weak_area_indices), max_topics - len(selected))
        selected.extend(weak_area_indices[:weak_to_add])
        
        # Add high importance topics
        remaining_slots = max_topics - len(selected)
        high_to_add = min(remaining_slots, len(high_importance_indices))
        selected.extend(high_importance_indices[:high_to_add])
        
        # Add medium importance topics
        remaining_slots = max_topics - len(selected)
        medium_to_add = min(remaining_slots, len(medium_importance_indices))
        selected.extend(medium_importance_indices[:medium_to_add])
        
        # Fill remaining slots with any topics
        remaining_slots = max_topics - len(selected)
        all_other_indices = [i for i in range(len(remaining_topics)) 
                           if i not in weak_area_indices 
                           and i not in high_importance_indices 
                           and i not in medium_importance_indices]
        
        remaining_to_add = min(remaining_slots, len(all_other_indices))
        selected.extend(all_other_indices[:remaining_to_add])
        
        return selected[:max_topics]
    
    def _select_review_topics(self, previous_schedule: List[Dict], current_day: int) -> List[Dict]:
        """
        Select topics for review based on spaced repetition algorithm
        """
        review_topics = []
        
        # Determine which days to review based on spaced repetition intervals
        review_intervals = []
        for interval in self.spaced_repetition_intervals:
            review_day = current_day - interval
            if review_day > 0 and review_day <= len(previous_schedule):
                review_intervals.append(review_day - 1)  # Convert to 0-indexed
        
        # Get topics from review days
        for day_idx in review_intervals:
            if day_idx < len(previous_schedule):
                day_schedule = previous_schedule[day_idx]
                for topic in day_schedule.get('topics', []):
                    # Add as review topic with different properties
                    review_topic = topic.copy()
                    review_topic['is_review'] = True
                    review_topic['study_duration_hours'] *= 0.5  # Less time for review
                    review_topics.append(review_topic)
        
        return review_topics
    
    def _calculate_study_duration(self, topic: Dict[str, Any]) -> float:
        """
        Calculate recommended study duration based on topic characteristics
        """
        base_duration = 1.0  # hours
        
        # Increase duration for weak areas
        if topic.get('is_weak_area'):
            base_duration *= 1.5
        
        # Adjust based on importance
        importance = topic.get('importance', 0.5)
        if importance > 0.8:
            base_duration *= 1.3
        elif importance > 0.5:
            base_duration *= 1.1
        
        # Ensure reasonable bounds
        return min(max(base_duration, 0.5), 4.0)  # Between 0.5 and 4 hours
    
    def adjust_study_plan(self, 
                         original_plan: Dict[str, Any], 
                         user_progress: Dict[str, Any], 
                         db: Session) -> Dict[str, Any]:
        """
        Dynamically adjust the study plan based on user progress and performance
        """
        # Analyze user progress
        completed_days = user_progress.get('days_completed', 0)
        completed_topics = user_progress.get('completed_topics', [])
        understanding_scores = user_progress.get('understanding_scores', {})
        time_taken = user_progress.get('time_taken', {})
        
        # Calculate performance metrics
        avg_understanding = sum(understanding_scores.values()) / len(understanding_scores) if understanding_scores else 0.5
        avg_time_efficiency = sum(time_taken.values()) / len(time_taken) if time_taken else 1.0
        
        # Identify areas needing adjustment
        struggling_topics = [topic for topic, score in understanding_scores.items() if score < 0.6]
        efficient_topics = [topic for topic, score in understanding_scores.items() if score > 0.8]
        
        # Create adjusted plan
        adjusted_schedule = []
        
        for day_schedule in original_plan['daily_schedule']:
            adjusted_day = day_schedule.copy()
            
            # Adjust topics based on performance
            adjusted_topics = []
            for topic in day_schedule.get('topics', []):
                topic_name = topic['name']
                
                # Adjust duration based on understanding
                if topic_name in struggling_topics:
                    # Spend more time on difficult topics
                    topic_copy = topic.copy()
                    topic_copy['study_duration_hours'] *= 1.3
                    topic_copy['needs_extra_attention'] = True
                    adjusted_topics.append(topic_copy)
                elif topic_name in efficient_topics:
                    # Spend less time on well-understood topics
                    topic_copy = topic.copy()
                    topic_copy['study_duration_hours'] *= 0.8
                    adjusted_topics.append(topic_copy)
                else:
                    adjusted_topics.append(topic)
            
            adjusted_day['topics'] = adjusted_topics
            adjusted_day['recommended_hours'] = sum([t.get('study_duration_hours', 1) for t in adjusted_topics])
            
            adjusted_schedule.append(adjusted_day)
        
        # Update the plan
        adjusted_plan = original_plan.copy()
        adjusted_plan['daily_schedule'] = adjusted_schedule
        adjusted_plan['adjustment_reasons'] = {
            'struggling_topics': struggling_topics,
            'efficient_topics': efficient_topics,
            'avg_understanding': avg_understanding,
            'adjustment_made_at': datetime.now().isoformat()
        }
        
        return adjusted_plan
    
    def get_topic_sequencing(self, 
                           topics: List[Dict[str, Any]], 
                           prerequisites: Dict[str, List[str]] = None) -> List[str]:
        """
        Generate optimal topic sequencing based on dependencies and difficulty
        """
        if not prerequisites:
            prerequisites = {}
        
        # Create a dependency graph
        from collections import defaultdict, deque
        
        graph = defaultdict(list)
        in_degree = {topic['name']: 0 for topic in topics}
        
        # Add prerequisite relationships
        for topic_name, prereqs in prerequisites.items():
            for prereq in prereqs:
                if prereq in in_degree:
                    graph[prereq].append(topic_name)
                    in_degree[topic_name] += 1
        
        # Topological sort with priority consideration
        queue = deque([topic['name'] for topic in topics if in_degree[topic['name']] == 0])
        sequence = []
        
        while queue:
            current = queue.popleft()
            sequence.append(current)
            
            for neighbor in graph[current]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        # If there are cycles, append remaining topics
        remaining = [topic['name'] for topic in topics if in_degree[topic['name']] > 0]
        sequence.extend(remaining)
        
        return sequence
