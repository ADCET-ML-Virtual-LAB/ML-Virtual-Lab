import asyncio
from sqlalchemy.orm import Session
from app.database import SessionLocal, engine, Base
from app.models.experiment import Experiment, ExperimentEvaluationSpec
from app.models.quiz import Quiz, QuizType, RevealPolicy, Question, Option

# The 10 experiments defined in the content reference
EXPERIMENTS = [
    {
        "title": "Artificial Neural Network",
        "slug": "artificial-neural-network",
        "aim": "To understand the working of Artificial Neural Networks.",
        "objective": "To implement and train an ANN model for a given dataset.",
        "order_index": 1,
    },
    {
        "title": "Single Layer Perceptron",
        "slug": "single-layer-perceptron",
        "aim": "To understand the working of a Single Layer Perceptron.",
        "objective": "To implement a Single Layer Perceptron algorithm for linearly separable data.",
        "order_index": 2,
    },
    {
        "title": "Linear Regression",
        "slug": "linear-regression",
        "aim": "To understand Linear Regression for predicting continuous values.",
        "objective": "To implement Simple and Multiple Linear Regression.",
        "order_index": 3,
    },
    {
        "title": "K-Means Clustering",
        "slug": "kmeans-clustering",
        "aim": "To understand the K-Means Clustering algorithm.",
        "objective": "To implement K-Means clustering and group unlabeled data.",
        "order_index": 4,
    },
    {
        "title": "K-Means Optimization",
        "slug": "kmeans-optimization",
        "aim": "To optimize the K-Means Clustering algorithm.",
        "objective": "To implement optimization techniques like Elbow method for K-Means.",
        "order_index": 5,
    },
    {
        "title": "Naive Bayes",
        "slug": "naive-bayes",
        "aim": "To understand the Naive Bayes classifier.",
        "objective": "To implement the Naive Bayes algorithm for classification tasks.",
        "order_index": 6,
    },
    {
        "title": "Find-S Algorithm",
        "slug": "find-s-algorithm",
        "aim": "To understand the Find-S algorithm for concept learning.",
        "objective": "To implement the Find-S algorithm to find the most specific hypothesis.",
        "order_index": 7,
    },
    {
        "title": "Multi Layer Perceptron",
        "slug": "multi-layer-perceptron",
        "aim": "To understand the working of a Multi Layer Perceptron.",
        "objective": "To implement an MLP and backpropagation algorithm.",
        "order_index": 8,
    },
    {
        "title": "Hierarchical Clustering",
        "slug": "hierarchical-clustering",
        "aim": "To understand Hierarchical Clustering algorithms.",
        "objective": "To implement agglomerative hierarchical clustering.",
        "order_index": 9,
    },
    {
        "title": "Decision Tree ID3",
        "slug": "decision-tree-id3",
        "aim": "To understand the Decision Tree classifier and ID3 algorithm.",
        "objective": "To implement the ID3 algorithm for building a decision tree.",
        "order_index": 10,
    }
]

def seed_experiments():
    db: Session = SessionLocal()
    try:
        for exp_data in EXPERIMENTS:
            # Check if exists
            existing = db.query(Experiment).filter(Experiment.slug == exp_data["slug"]).first()
            if existing:
                print(f"Experiment {exp_data['slug']} already exists. Skipping.")
                continue
            
            print(f"Creating experiment {exp_data['slug']}...")
            
            exp = Experiment(
                title=exp_data["title"],
                slug=exp_data["slug"],
                aim=exp_data["aim"],
                objective=exp_data["objective"],
                order_index=exp_data["order_index"],
                is_published=True,
                notes=f"## {exp_data['title']} Theory\n\nThis is a placeholder for theory notes.\n\n### References\n- Reference 1\n- Reference 2",
                video_url="",
                starter_code="# Write your code here\n\ndef main():\n    pass\n\nif __name__ == '__main__':\n    main()",
                allowed_imports=["numpy", "pandas", "sklearn"]
            )
            db.add(exp)
            db.flush()
            
            # Create a simple pre-quiz
            pre_quiz = Quiz(
                experiment_id=exp.id,
                quiz_type=QuizType.pre,
                is_scored=False,
                title="Pre-Quiz",
                reveal_policy=RevealPolicy.immediate
            )
            db.add(pre_quiz)
            db.flush()
            
            q1 = Question(quiz_id=pre_quiz.id, question_text="What is a key concept here?", order_index=1)
            db.add(q1)
            db.flush()
            db.add(Option(question_id=q1.id, option_text="Option A", is_correct=True, order_index=1))
            db.add(Option(question_id=q1.id, option_text="Option B", is_correct=False, order_index=2))
            
            # Create evaluation spec
            eval_spec = ExperimentEvaluationSpec(
                experiment_id=exp.id,
                expected_output={"status": "success"}
            )
            db.add(eval_spec)
            
        db.commit()
        print("Done seeding experiments!")
    finally:
        db.close()

if __name__ == "__main__":
    seed_experiments()
