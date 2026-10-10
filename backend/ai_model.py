import pandas as pd
from sklearn.tree import DecisionTreeClassifier


# Sample training data
# HIGH = needs more study attention
# MEDIUM = needs moderate attention
# LOW = needs less attention

data = {
    "score": [
        35, 40, 45, 48,
        55, 60, 65, 68,
        72, 78, 85, 90
    ],

    "attendance": [
        60, 65, 70, 72,
        70, 75, 80, 82,
        85, 88, 92, 95
    ],

    "study_hours": [
        1, 1, 1.5, 1.5,
        2, 2, 2.5, 2.5,
        3, 3.5, 4, 5
    ],

    "previous_score": [
        45, 50, 52, 55,
        60, 62, 65, 60,
        70, 75, 80, 85
    ],

    "priority": [
        "HIGH", "HIGH", "HIGH", "HIGH",
        "MEDIUM", "MEDIUM", "MEDIUM", "MEDIUM",
        "LOW", "LOW", "LOW", "LOW"
    ]
}


# Convert the training data into a Pandas DataFrame
df = pd.DataFrame(data)


# Input features
X = df[
    [
        "score",
        "attendance",
        "study_hours",
        "previous_score"
    ]
]


# Target
y = df["priority"]


# Create Decision Tree model
model = DecisionTreeClassifier(
    random_state=42,
    max_depth=4
)


# Train the model
model.fit(X, y)


def predict_priority(
    score,
    attendance,
    study_hours,
    previous_score
):
    """
    Predict the study priority for a student.
    """

    input_data = pd.DataFrame([
        {
            "score": score,
            "attendance": attendance,
            "study_hours": study_hours,
            "previous_score": previous_score
        }
    ])

    prediction = model.predict(input_data)

    return prediction[0]