// Read-only quiz for instructors: every question with its options and the
// correct answer marked. Nothing can be selected or submitted here.
export default function AnswerKey({ quiz, emptyText }) {
  if (!quiz || quiz.questions.length === 0) {
    return <p className="ic-placeholder">{emptyText}</p>;
  }

  return (
    <ol className="ic-quiz">
      {quiz.questions.map((question) => (
        <li key={question.id} className="ic-quiz__question">
          <p className="ic-quiz__text">{question.question_text}</p>
          <ul className="ic-quiz__options">
            {question.options.map((option) => (
              <li
                key={option.id}
                className={`ic-quiz__option${option.is_correct ? " ic-quiz__option--correct" : ""}`}
              >
                <span>{option.option_text}</span>
                {option.is_correct && <span className="badge badge--green">Correct answer</span>}
              </li>
            ))}
          </ul>
        </li>
      ))}
    </ol>
  );
}
