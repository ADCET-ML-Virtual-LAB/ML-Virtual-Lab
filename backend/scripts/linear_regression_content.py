"""Content for the Linear Regression experiment (loaded as experiment number 8).

Edit the text here and re-run `python -m scripts.load_linear_regression` to refresh it.
"""

SLUG = "linear-regression-experiment"
ORDER_INDEX = 8

TITLE = "Linear Regression"

# One overview: the Home Overview and the Basic Details overview combined (no repeated sentences).
OVERVIEW = (
    "Linear Regression is a supervised machine learning algorithm used to predict continuous numerical values "
    "by learning the relationship between input features and an output variable. It is one of the fundamental "
    "algorithms in machine learning and is widely used for tasks such as predicting house prices, sales revenue, "
    "electricity consumption, and student marks. In this experiment, students will learn how Linear Regression "
    "works, understand the mathematical equation of a regression model, distinguish between simple and multiple "
    "linear regression, and interpret predictions and errors. The experiment introduces the concepts of simple and "
    "multiple linear regression, the best-fitting line, model coefficients, predictions, residuals, and evaluation "
    "metrics, and also covers the practical applications and limitations of Linear Regression."
)

AIM = (
    "To understand the working principle and mathematical foundation of Linear Regression and learn how it can be "
    "used to predict continuous numerical values from input data."
)

OBJECTIVE = (
    "After completing this experiment, students will be able to: explain the concept and purpose of Linear "
    "Regression; differentiate between regression and classification; understand the equations of simple and "
    "multiple linear regression; interpret slope, intercept, coefficients, predictions, and residuals; explain how "
    "a regression model is trained and evaluated; and identify practical applications and limitations of Linear "
    "Regression."
)

VIDEO_URL = "https://www.youtube.com/watch?v=nk2CQITm_eo"

NOTES = """# Theory: Linear Regression

## 1. Introduction to Supervised Learning

Supervised learning is a type of machine learning in which a model learns from labelled training data. Each training example contains input features and a known output or target value. The model uses these examples to learn a relationship that can be used to make predictions for new data.

Supervised learning problems are commonly divided into two categories:

- **Regression:** Predicts continuous numerical values, such as house prices, temperature, or sales revenue.
- **Classification:** Predicts discrete classes or categories, such as whether an email is spam or not spam.

Linear Regression is a supervised learning algorithm primarily used for regression problems.

## 2. What Is Linear Regression?

Linear Regression is a statistical and machine learning technique that represents the relationship between input variables and a numerical target using a linear equation.

For example, a student's study hours may be related to their examination marks. A Linear Regression model can learn this relationship from previous observations and estimate the marks associated with a given number of study hours.

Other applications include house-price prediction, sales forecasting, electricity demand estimation, and production-cost analysis.

The model aims to find a line, or a higher-dimensional linear relationship, that fits the observed data as well as possible.

## 3. Simple Linear Regression

Simple Linear Regression uses **one independent variable** to predict **one dependent variable**.

Its equation is:

**ŷ = mx + c**

Where:

- **x:** Input or independent variable.
- **ŷ:** Predicted output.
- **m:** Slope of the line.
- **c:** Intercept, or the predicted output when x equals zero.

For example, suppose a model predicts examination marks using study hours:

**Predicted marks = 8 × Study Hours + 30**

If a student studies for 4 hours, the predicted marks are:

**ŷ = 8 × 4 + 30 = 62**

Therefore, the model predicts 62 marks.

The slope of 8 means the predicted marks increase by 8 for every additional study hour in this example. The intercept of 30 is the model's predicted mark at zero study hours. These are learned model parameters, and the relationship should not automatically be interpreted as proof of causation.

## 4. Multiple Linear Regression

Multiple Linear Regression uses **two or more independent variables** to predict a numerical output.

Its general equation is:

**ŷ = b₀ + b₁x₁ + b₂x₂ + ... + bₙxₙ**

Where:

- **ŷ:** Predicted output.
- **b₀:** Intercept.
- **b₁, b₂, ..., bₙ:** Learned coefficients.
- **x₁, x₂, ..., xₙ:** Input features.

For example, a house-price model may use floor area, number of bedrooms, and property age to estimate the price.

Each coefficient describes the model's predicted change in output for a one-unit change in the corresponding feature, while the other included features are held constant.

## 5. Best-Fitting Line

A best-fitting line represents the relationship that the model has learned from the training data. In ordinary least-squares Linear Regression, the model chooses its coefficients to minimize the **sum of squared residuals** on the training data.

A residual is the difference between an observed value and the model's predicted value.

**Residual = Actual Value − Predicted Value**

For example, if the actual value is 70 and the predicted value is 65:

**Residual = 70 − 65 = +5**

A positive residual means the prediction was below the actual value. A negative residual means the prediction was above the actual value.

Squaring residuals prevents positive and negative errors from cancelling each other and gives greater weight to larger errors.

## 6. How Linear Regression Works

The general workflow is:

1. **Collect data:** Obtain examples containing input features and known target values.
2. **Prepare the data:** Check missing values, incorrect entries, feature types, and data quality.
3. **Separate the data:** Use training data to fit the model and separate test data to assess its performance.
4. **Train the model:** Learn the intercept and coefficients from the training examples.
5. **Make predictions:** Apply the learned relationship to new input values.
6. **Evaluate performance:** Compare predicted values with actual values using suitable metrics.
7. **Interpret results:** Examine the learned relationship, prediction errors, and limitations.

The test set should not be used to fit the model. Keeping it separate provides a more useful estimate of how the model may perform on unseen data.

## 7. Important Functions and Attributes

Python's Scikit-learn library provides a standard implementation of ordinary least-squares Linear Regression through the `LinearRegression` class.

- **`LinearRegression()`** creates a Linear Regression model.
- **`fit(X, y)`** trains the model using input features `X` and target values `y`.
- **`predict(X)`** estimates target values for the supplied input features.
- **`coef_`** provides the learned coefficient or coefficients.
- **`intercept_`** provides the learned intercept.

Here, `X` represents the input feature data, while `y` represents the known target values during training.

## 8. Evaluating a Linear Regression Model

A model should be evaluated using data that was not used to train it. Common evaluation metrics include:

**Mean Absolute Error (MAE):** The average absolute difference between actual and predicted values. It is expressed in the same units as the target.

**Mean Squared Error (MSE):** The average of squared prediction errors. It penalizes larger errors more heavily and is expressed in squared target units.

**R-squared (R²):** Measures how well the model explains variation in the target relative to a baseline that predicts the training-set mean. A value of 1 indicates a perfect fit on the evaluated data, 0 indicates performance equivalent to that baseline, and a negative value means the model performs worse than the baseline. R² is not a percentage accuracy score.

No single metric describes every aspect of model performance, so the choice of metric should match the problem.

## 9. Visualizing Linear Regression

A scatter plot can display observed input-output pairs, while a regression line shows the relationship predicted by the model. The vertical distance between an observed point and the line represents its residual.

If the line captures the overall pattern, it may be useful for prediction. However, visible patterns in the residuals, extreme outliers, or curved relationships may indicate that a simple linear model is not suitable.

## 10. Applications of Linear Regression

Linear Regression is used in many fields:

- **Real estate:** Estimating property prices from property features.
- **Retail:** Forecasting sales based on relevant business variables.
- **Energy:** Estimating electricity consumption.
- **Education:** Studying relationships between study time and examination marks.
- **Manufacturing:** Estimating production costs or process measurements.
- **Business analytics:** Understanding numerical trends and relationships.

## 11. Advantages and Limitations

### Advantages

- Simple to understand and interpret.
- Computationally efficient for many datasets.
- Provides coefficients that help explain the fitted relationship.
- Offers a useful baseline for numerical prediction tasks.

### Limitations

- May perform poorly when the relationship is strongly nonlinear.
- Can be affected by outliers and influential observations.
- Strong relationships between input features can make individual coefficients difficult to interpret.
- Predictions outside the observed data range may be unreliable.
- Missing, noisy, or unrepresentative data can reduce performance.

## Conclusion

Linear Regression is a foundational supervised learning algorithm for predicting continuous numerical values. Understanding its equations, coefficients, residuals, training procedure, and evaluation metrics provides a foundation for studying more advanced machine learning methods.

## References

1. Scikit-learn, Linear Models — Linear Regression: https://scikit-learn.org/stable/modules/linear_model.html#ordinary-least-squares
2. Scikit-learn, LinearRegression API Reference: https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.LinearRegression.html
3. StatQuest, Linear Regression, Clearly Explained!!!: https://www.youtube.com/watch?v=nk2CQITm_eo
"""

# ── Quizzes: (question, [options], index of the correct option) ───────────────

PRE_QUIZ = [
    ("What is machine learning?",
     ["A method of storing files", "A field that enables computers to learn patterns from data",
      "A programming language", "A type of computer hardware"], 1),
    ("Which of the following is an example of a numerical value?",
     ["Apple", "Red", "85.5", "Yes"], 2),
    ("Which type of machine learning uses labelled training data?",
     ["Supervised learning", "Unsupervised learning", "Reinforcement learning only", "Random search"], 0),
    ("Which task is an example of predicting a continuous numerical value?",
     ["Identifying whether an email is spam", "Recognizing a cat in an image",
      "Predicting tomorrow's temperature", "Classifying a fruit as an apple or orange"], 2),
    ("In a prediction problem, what is an input feature?",
     ["The value the model must predict", "Information used by the model to make a prediction",
      "The final model accuracy", "An error made by the model"], 1),
    ("What is the purpose of a mathematical equation?",
     ["To represent a relationship using mathematical symbols", "To store images",
      "To remove all errors from data", "To guarantee a correct prediction"], 0),
    ("In the equation y = 2x + 3, what is the value of y when x = 4?",
     ["8", "9", "11", "12"], 2),
    ("What does a graph help us do?",
     ["Visualize relationships and patterns in data", "Guarantee that a model is correct",
      "Automatically remove every outlier", "Replace the need for data"], 0),
    ("Which of the following is a machine learning application?",
     ["Predicting house prices from property data", "Typing a document manually",
      "Turning on a light using a switch", "Copying a file from one folder to another"], 0),
    ("True or False: Machine learning models can learn patterns from data to make predictions.",
     ["True", "False"], 0),
]

POST_QUIZ = [
    ("What is the primary purpose of Linear Regression?",
     ["To predict continuous numerical values", "To classify images into categories only",
      "To encrypt data", "To group data without using any target values"], 0),
    ("Which equation represents Simple Linear Regression?",
     ["ŷ = mx + c", "ŷ = x² + y²", "ŷ = m + x²", "ŷ = x / 0"], 0),
    ("What does the slope represent in the equation ŷ = mx + c?",
     ["The number of training examples", "The predicted change in output for a one-unit increase in input",
      "The number of features in every model", "The total number of prediction errors"], 1),
    ("In the equation ŷ = mx + c, what does c represent?",
     ["The slope", "The input feature", "The intercept", "The residual"], 2),
    ("True or False: Multiple Linear Regression uses two or more independent variables to predict a numerical output.",
     ["True", "False"], 0),
    ("A model predicts 75 marks, while the actual marks are 80. What is the residual?",
     ["−5", "0", "+5", "+155"], 2),
    ("What does the `fit()` method do in Scikit-learn's Linear Regression model?",
     ["Trains the model using the supplied data", "Displays a graph automatically in every case",
      "Deletes the training data", "Calculates only the test-set accuracy"], 0),
    ("Which attribute provides the learned coefficient or coefficients?",
     ["`predict()`", "`fit()`", "`coef_`", "`intercept_`"], 2),
    ("Which statement about Mean Absolute Error (MAE) is correct?",
     ["It measures the average absolute prediction error", "It always equals R²",
      "It measures the number of input features", "It is always expressed as a percentage"], 0),
    ("True or False: An R² score of 0 always means that a model makes no prediction errors.",
     ["True", "False"], 1),
]

ASSIGNMENT = [
    ("A student builds a model to predict examination marks based on study hours. Which variable is most likely to be the target variable?",
     ["Study hours", "Examination marks", "Number of textbooks", "Student roll number"], 1),
    ("A Linear Regression model is represented by the equation ŷ = 5x + 20, where x represents study hours. What is the predicted output for 6 study hours?",
     ["30", "40", "50", "60"], 2),
    ("A house-price model uses floor area as its only input feature. Which type of Linear Regression does it use?",
     ["Multiple Linear Regression", "Simple Linear Regression", "Logistic Regression", "Classification"], 1),
    ("A model predicts a house price of ₹45 lakh, while the actual price is ₹50 lakh. Using the definition residual = actual − predicted, what is the residual?",
     ["−₹5 lakh", "₹0", "+₹5 lakh", "+₹95 lakh"], 2),
    ("A real-estate company wants to estimate house prices using floor area, number of bedrooms, and property age. Which approach is most appropriate among the following?",
     ["Simple Linear Regression with floor area only", "Multiple Linear Regression using all three features",
      "Classification into spam and non-spam", "A model that does not use input features"], 1),
    ("A model has a Mean Absolute Error (MAE) of 4 marks on an examination dataset. What does this indicate?",
     ["Every prediction is exactly 4 marks wrong", "The average absolute prediction error is 4 marks",
      "The model has 4% accuracy", "The model always predicts 4 marks"], 1),
    ("A Linear Regression model produces an R² score of −0.2 on a test dataset. What is the most appropriate interpretation?",
     ["The model is 20% accurate",
      "The model performs worse than the baseline that predicts the training-set mean",
      "The model has no prediction errors", "The model correctly predicts 20% of the values"], 1),
    ("A model performs well on houses with floor areas between 500 and 2,000 square feet. It is then used to predict the price of a house with an area of 10,000 square feet. What is the main concern?",
     ["The model cannot accept numerical inputs",
      "The prediction is outside the observed training range and may be unreliable",
      "Linear Regression can only predict categories", "The intercept automatically becomes zero"], 1),
    ("A dataset contains several extreme outliers, and the fitted regression line is strongly influenced by them. Which statement is correct?",
     ["Ordinary least-squares Linear Regression can be sensitive to outliers",
      "Linear Regression is completely unaffected by outliers",
      "Outliers always improve model performance",
      "Outliers guarantee a higher R² score on unseen data"], 0),
    ("True or False: A Linear Regression model should be evaluated only on the same data used to train it.",
     ["True", "False"], 1),
]

# ── Code Exercise ─────────────────────────────────────────────────────────────

ALLOWED_IMPORTS = ["numpy", "pandas", "sklearn"]

# The dataset file (committed in frontend/public/datasets/ and served by the app). The code runner
# copies it into the browser's Python environment under its file name, so students load it with
# pd.read_csv("Salary_dataset.csv").
DATASET_URL = "/datasets/Salary_dataset.csv"
DATASET_FILE = "Salary_dataset.csv"

CODE_PROBLEM_STATEMENT = """## Problem Statement

Use **Linear Regression** to predict a person's salary from their years of experience.

The dataset file `Salary_dataset.csv` (30 records with the columns `YearsExperience` and `Salary`) is available to your code. Load it with `pd.read_csv("Salary_dataset.csv")`.

### Steps

1. Load the dataset. Use `YearsExperience` as the input feature `X` (keep it two-dimensional, for example `data[["YearsExperience"]]`) and `Salary` as the target `y`.
2. Split the data into training and test subsets with `train_test_split(X, y, test_size=0.2, random_state=42)`. Use exactly this test size and this random state.
3. Create a `LinearRegression` model and train it on the training subset.
4. Predict the salaries for the test subset.
5. Round each prediction to 2 decimal places and store the list of predictions, in the order the test subset is returned, in the variable `result`.

### Important

- The answer must be stored in the variable `result` (a list of numbers). It is already created for you in the editor.
- Use only the random state mentioned above. A different value gives a different split and a different answer.
- Click Run to see your output. Submit shows whether your `result` matches the expected result. Click Mark Completed when you have finished this exercise.
"""

# What the student sees in the editor.
STARTER_CODE = (
    "result = None  # store your final answer in this variable\n"
    "\n"
    "# Write your code here\n"
)

# A complete working solution (what a student is expected to write). Used for the demo
# and by the tests to confirm the stored expected result. It reads Salary_dataset.csv from
# the current directory, as the student's code does in the browser.
SOLUTION_CODE = (
    "import pandas as pd\n"
    "from sklearn.model_selection import train_test_split\n"
    "from sklearn.linear_model import LinearRegression\n"
    "\n"
    "# Load the dataset\n"
    "data = pd.read_csv(\"Salary_dataset.csv\")\n"
    "\n"
    "# Input feature (2-D) and target\n"
    "X = data[[\"YearsExperience\"]]\n"
    "y = data[\"Salary\"]\n"
    "\n"
    "# Split the data: 80% training, 20% test, random_state=42\n"
    "X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)\n"
    "\n"
    "# Train the model\n"
    "model = LinearRegression()\n"
    "model.fit(X_train, y_train)\n"
    "\n"
    "# Predict the test subset and keep the answer in `result`\n"
    "predictions = model.predict(X_test)\n"
    "result = [round(float(p), 2) for p in predictions]\n"
    "print(result)\n"
)

# Produced by SOLUTION_CODE (scikit-learn, random_state=42, test_size=0.2).
EXPECTED_RESULT = [115791.21, 71499.28, 102597.87, 75268.8, 55478.79, 60190.7]
