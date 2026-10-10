from ai_model import predict_priority
from recommendations import generate_study_plan


# Test student data
score = 48
attendance = 70
study_hours = 1
previous_score = 55


# Get ML prediction
priority = predict_priority(
    score,
    attendance,
    study_hours,
    previous_score
)


# Create a sample recommendation
recommendations = [
    {
        "subject_id": 3,
        "subject_name": "Data Structures",
        "topic": "Arrays and Linked Lists",
        "score": score,
        "priority": priority,
        "recommendation": "Very low score, Low attendance, Increase study hours"
    }
]


# Generate study plan
study_plan = generate_study_plan(recommendations)


print("Predicted Study Priority:", priority)
print("Generated Study Plan:")
print(study_plan)