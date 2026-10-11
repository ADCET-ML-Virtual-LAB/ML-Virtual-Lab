import { useState } from "react";
import { quizzesApi } from "../api/quizzes.js";
import "./QuizPanel.css";

/**
 * QuizPanel — reused for pre-quiz, post-quiz, and graded assignment.
 *
 * Props:
 *   quiz        — quiz object from the backend (questions + options, no is_correct for students)
 *   quizType    — "pre" | "post" | "assignment"
 *   onComplete  — called with the submit response after successful submission
 *   readOnly    — true for instructors/admins: they can view, but not answer or submit
 */
export default function QuizPanel({ quiz, quizType, onComplete, readOnly = false }) {
  const [answers, setAnswers] = useState({}); // { question_id: option_id }
  const [result, setResult] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [bestScore, setBestScore] = useState(quiz.my_best_score ?? null);

  const label = quizType === "pre" ? "Pre-Quiz" : quizType === "post" ? "Post-Quiz" : "Assignment";
  const isGraded = quizType === "assignment";

  function selectOption(questionId, optionId) {
    if (result || readOnly) return; // already submitted, or view-only
    setAnswers((prev) => ({ ...prev, [questionId]: optionId }));
  }

  async function handleSubmit() {
    if (Object.keys(answers).length < quiz.questions.length) {
      setError("Please answer all questions before submitting.");
      return;
    }
    setError("");
    setSubmitting(true);
    try {
      const answersPayload = Object.entries(answers).map(([question_id, selected_option_id]) => ({
        question_id,
        selected_option_id,
      }));
      const res = await quizzesApi.submit(quiz.id, answersPayload);
      setResult(res);
      if (res.best_score != null) setBestScore(res.best_score);
      onComplete?.(res);
    } catch (err) {
      setError(err.response?.data?.detail || "Submission failed. Please try again.");
    } finally {
      setSubmitting(false);
    }
  }

  function getOptionClass(question, option) {
    let cls = "quiz-option";
    if (answers[question.id] === option.id) cls += " quiz-option--selected";
    if (result) {
      const answerResult = result.answers.find((a) => a.question_id === question.id);
      if (answerResult) {
        if (option.id === answers[question.id]) {
          cls += answerResult.is_correct ? " quiz-option--correct" : " quiz-option--wrong";
        }
      }
    }
    return cls;
  }

  // The assignment can be submitted only once: reopening it shows the saved state, not the form.
  if (isGraded && !result && quiz.my_attempts > 0) {
    return (
      <div className="quiz-panel">
        <div className="quiz-panel__header">
          <h3 className="quiz-panel__title">{quiz.title || label}</h3>
          <span className="badge badge--blue">Graded</span>
        </div>
        <div className="quiz-result">
          <div className="quiz-result__score">
            {quiz.my_best_score != null ? (
              <>
                You have already submitted this assignment. Score: <strong>{quiz.my_best_score}%</strong>
              </>
            ) : (
              "You have already submitted this assignment. Your score will be shown after the deadline."
            )}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="quiz-panel">
      <div className="quiz-panel__header">
        <h3 className="quiz-panel__title">{quiz.title || label}</h3>
        {isGraded && <span className="badge badge--blue">Graded</span>}
      </div>

      {!isGraded && bestScore != null && (
        <p className="quiz-panel__best">
          Best score so far: <strong>{bestScore}%</strong> (unlimited attempts, for your own practice)
        </p>
      )}

      {quiz.questions.map((question, qi) => (
        <div key={question.id} className="quiz-question">
          <p className="quiz-question__text">
            <strong>Q{qi + 1}.</strong> {question.question_text}
          </p>
          <div className="quiz-options">
            {question.options
              .slice()
              .sort((a, b) => a.order_index - b.order_index)
              .map((option) => (
                <button
                  key={option.id}
                  className={getOptionClass(question, option)}
                  onClick={() => selectOption(question.id, option.id)}
                  disabled={!!result || readOnly}
                >
                  {option.option_text}
                </button>
              ))}
          </div>
        </div>
      ))}

      {error && <div className="alert alert--error">{error}</div>}

      {readOnly ? (
        <div className="quiz-readonly">View only: only students can answer and submit quizzes.</div>
      ) : !result ? (
        <button
          className="btn btn--primary"
          onClick={handleSubmit}
          disabled={submitting}
        >
          {submitting ? "Submitting…" : "Submit"}
        </button>
      ) : (
        <div className="quiz-result">
          {isGraded && result.score != null ? (
            <div className="quiz-result__score">
              Score: <strong>{result.score}%</strong> (attempt #{result.attempt_number})
            </div>
          ) : isGraded ? (
            <div className="quiz-result__score">
              Submitted (score will be revealed after the deadline).
            </div>
          ) : (
            <div className="quiz-result__score">
              {result.answers.filter((a) => a.is_correct).length} / {result.answers.length} correct
              {result.score != null && <> ({result.score}%)</>}
              &nbsp;— attempt #{result.attempt_number}
            </div>
          )}
          {!isGraded && (
            <button
              className="btn btn--ghost btn--sm"
              onClick={() => { setResult(null); setAnswers({}); }}
            >
              Retry
            </button>
          )}
        </div>
      )}
    </div>
  );
}
