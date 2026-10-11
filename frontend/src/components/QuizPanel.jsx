import { useState } from "react";
import { quizzesApi } from "../api/quizzes.js";
import "./QuizPanel.css";

/**
 * QuizPanel — reused for pre-quiz, post-quiz, and graded assignment.
 *
 * Pre/post quizzes show an introduction first. After a submission, the current
 * attempt score is shown alongside the saved best score. Leaving the section or
 * refreshing remounts this component, so the introduction shows only the saved
 * best score (not the previous attempt's transient result).
 *
 * Props:
 *   quiz             — quiz object from the backend
 *   quizType         — "pre" | "post" | "assignment"
 *   experimentNumber — experiment order number for the intro screen
 *   experimentTitle  — experiment title for the intro screen
 *   onComplete       — refreshes authoritative experiment/progress data
 *   readOnly         — true for instructors/admins
 */
export default function QuizPanel({
  quiz,
  quizType,
  experimentNumber,
  experimentTitle,
  onComplete,
  readOnly = false,
}) {
  const [answers, setAnswers] = useState({}); // { question_id: option_id }
  const [result, setResult] = useState(null); // transient current submission response only
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [syncWarning, setSyncWarning] = useState("");
  const [bestScore, setBestScore] = useState(quiz.my_best_score ?? null);
  const [hasStarted, setHasStarted] = useState(
    quizType === "assignment" || readOnly,
  );

  const label = quizType === "pre" ? "Pre-Quiz" : quizType === "post" ? "Post-Quiz" : "Assignment";
  const isGraded = quizType === "assignment";
  const isSelfAssessment = quizType === "pre" || quizType === "post";

  function selectOption(questionId, optionId) {
    if (result || readOnly || submitting) return;
    setAnswers((prev) => ({ ...prev, [questionId]: optionId }));
  }

  async function handleSubmit() {
    if (Object.keys(answers).length < quiz.questions.length) {
      setError("Please answer all questions before submitting.");
      return;
    }
    setError("");
    setSyncWarning("");
    setSubmitting(true);
    try {
      const answersPayload = Object.entries(answers).map(([question_id, selected_option_id]) => ({
        question_id,
        selected_option_id,
      }));
      const res = await quizzesApi.submit(quiz.id, answersPayload);

      // The response includes this attempt's score for immediate feedback and,
      // for pre/post quizzes, the persisted best score. Attempt details are not saved.
      setResult(res);
      if (res.best_score != null) setBestScore(res.best_score);

      // The completion tick must come from refreshed backend state, not from this
      // local submit result. ExperimentPage returns null when refresh fails.
      if (onComplete) {
        const refreshed = await onComplete(res);
        if (refreshed === null) {
          setSyncWarning(
            "Your submission was saved, but progress could not be refreshed. The completion tick will appear after the saved status is refreshed.",
          );
        }
      }
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
      const answerResult = result.answers?.find((a) => a.question_id === question.id);
      if (answerResult && option.id === answers[question.id]) {
        cls += answerResult.is_correct ? " quiz-option--correct" : " quiz-option--wrong";
      }
    }
    return cls;
  }

  function retryQuiz() {
    setAnswers({});
    setResult(null);
    setError("");
    setSyncWarning("");
    // For self-assessment, return to the introduction so every new attempt is
    // explicitly started with Start Now.
    setHasStarted(!isSelfAssessment || readOnly);
  }

  // The assignment can be submitted only once. Reopening it shows the saved result:
  // the score, then every question with the correct answer, the student's own
  // answer and whether it was correct. All of it comes from the backend.
  if (isGraded && !result && quiz.my_submitted) {
    const reviewByQuestion = new Map((quiz.my_review || []).map((r) => [r.question_id, r]));
    return (
      <div className="quiz-panel">
        <div className="quiz-panel__header">
          <h3 className="quiz-panel__title">{quiz.title || label}</h3>
          <span className="badge badge--blue">Submitted</span>
        </div>
        <div className="quiz-result">
          <div className="quiz-result__score">
            {quiz.my_assignment_score != null ? (
              <>Your score: <strong>{quiz.my_assignment_score}%</strong></>
            ) : (
              "The assignment was submitted, but its saved score is not available. Refresh the experiment to retrieve it."
            )}
          </div>
        </div>

        {quiz.questions.length > 0 && !quiz.my_review && (
          <div className="alert alert--warning" role="status">
            Your answers could not be loaded. Refresh the experiment to try again.
          </div>
        )}

        {quiz.my_review && quiz.questions.map((question, qi) => {
          const review = reviewByQuestion.get(question.id);
          const correctIds = review?.correct_option_ids || [];
          return (
            <div key={question.id} className="quiz-question quiz-review">
              <div className="quiz-review__head">
                <p className="quiz-question__text">
                  <strong>Q{qi + 1}.</strong> {question.question_text}
                </p>
                <span className={`badge ${review?.is_correct ? "badge--green" : "badge--red"}`}>
                  {review?.is_correct ? "Correct" : "Incorrect"}
                </span>
              </div>
              <div className="quiz-options">
                {question.options
                  .slice()
                  .sort((a, b) => a.order_index - b.order_index)
                  .map((option) => {
                    const isCorrectOption = correctIds.includes(option.id);
                    const isMine = review?.selected_option_id === option.id;
                    let cls = "quiz-option quiz-review__option";
                    if (isCorrectOption) cls += " quiz-option--correct";
                    else if (isMine) cls += " quiz-option--wrong";
                    return (
                      <div key={option.id} className={cls}>
                        <span>{option.option_text}</span>
                        <span className="quiz-review__tags">
                          {isMine && <em>Your answer</em>}
                          {isCorrectOption && <em>Correct answer</em>}
                        </span>
                      </div>
                    );
                  })}
              </div>
            </div>
          );
        })}
      </div>
    );
  }

  // Students see the quiz introduction first, including the saved best score.
  // This state is deliberately local/transient; returning to this tab or refreshing
  // reads best score and submitted status again from the backend.
  if (isSelfAssessment && !readOnly && !hasStarted) {
    return (
      <div className="quiz-panel">
        <div className="quiz-intro">
          <p className="quiz-intro__eyebrow">{label}</p>
          <h3 className="quiz-intro__title">{experimentTitle || quiz.title || label}</h3>
          <div className="quiz-intro__meta">
            <span>Experiment No.</span>
            <strong>{experimentNumber != null ? String(experimentNumber).padStart(2, "0") : "—"}</strong>
          </div>
          <div className="quiz-intro__score">
            <span className="quiz-intro__score-label">My best score</span>
            {bestScore != null ? (
              <strong className="quiz-intro__score-value">{bestScore}%</strong>
            ) : (
              <strong className="quiz-intro__not-attempted">Not attempted</strong>
            )}
          </div>
          <p className="quiz-intro__description">
            You can attempt this quiz again whenever you need. Your best score will be saved.
          </p>
          <button
            type="button"
            className="btn btn--primary quiz-intro__start"
            onClick={() => { setError(""); setSyncWarning(""); setHasStarted(true); }}
          >
            Start Now
          </button>
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

      {isSelfAssessment && bestScore != null && !result && (
        <p className="quiz-panel__best">Saved best score: <strong>{bestScore}%</strong></p>
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
                  type="button"
                  className={getOptionClass(question, option)}
                  onClick={() => selectOption(question.id, option.id)}
                  disabled={!!result || readOnly || submitting}
                >
                  {option.option_text}
                </button>
              ))}
          </div>
        </div>
      ))}

      {error && <div className="alert alert--error" role="alert">{error}</div>}
      {syncWarning && <div className="alert alert--warning" role="status">{syncWarning}</div>}

      {readOnly ? (
        <div className="quiz-readonly">View only: only students can answer and submit quizzes.</div>
      ) : !result ? (
        <button
          type="button"
          className="btn btn--primary"
          onClick={handleSubmit}
          disabled={submitting}
        >
          {submitting ? "Submitting…" : "Submit"}
        </button>
      ) : (
        <div className="quiz-result quiz-result--submitted">
          {isSelfAssessment ? (
            <>
              <div className="quiz-result__scores">
                <div className="quiz-result__score-item">
                  <span>This attempt</span>
                  <strong>{result.score != null ? `${result.score}%` : "Unavailable"}</strong>
                </div>
                <div className="quiz-result__score-item">
                  <span>My best score</span>
                  <strong>{result.best_score ?? bestScore ?? "—"}{(result.best_score ?? bestScore) != null ? "%" : ""}</strong>
                </div>
              </div>
              <button type="button" className="btn btn--ghost btn--sm" onClick={retryQuiz}>
                Try Again
              </button>
            </>
          ) : result.score != null ? (
            <div className="quiz-result__score">Score: <strong>{result.score}%</strong></div>
          ) : (
            <div className="quiz-result__score">Assignment submitted successfully. Your score is being retrieved.</div>
          )}
          {isGraded && <div className="quiz-result__score">Your assignment has been submitted.</div>}
        </div>
      )}
    </div>
  );
}
