import { useState, useEffect } from "react";
import { useParams } from "react-router-dom";
import { experimentsApi } from "../api/experiments.js";
import { useAuth } from "../context/AuthContext.jsx";
import QuizPanel from "../components/QuizPanel.jsx";
import GuidedLab from "../components/GuidedLab.jsx";
import CodeEditor from "../components/CodeEditor.jsx";
import "./ExperimentPage.css";

// The left-sidebar workspace will replace these tabs in the navigation refactor.
// Keep the same stable section keys so saved completion records remain valid.
const SECTIONS = [
  { id: "overview", label: "Title / Overview", completionKey: "overview" },
  { id: "aim", label: "Aim / Learning Objectives", completionKey: "aim-objectives" },
  { id: "pre-quiz", label: "Pre-Quiz" },
  { id: "video", label: "Video", completionKey: "video" },
  { id: "theory", label: "Theory / Reading Material", completionKey: "theory" },
  { id: "guided-lab", label: "Guided Lab", completionKey: "guided-lab" },
  { id: "code-editor", label: "Code Exercise" },
  { id: "post-quiz", label: "Post-Quiz" },
  { id: "assignment", label: "Assignment" },
];

export default function ExperimentPage() {
  const { slug } = useParams();
  const { user } = useAuth();
  const isStudent = user?.role === "student";
  const [experiment, setExperiment] = useState(null);
  const [activeSection, setActiveSection] = useState("overview");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [savingSection, setSavingSection] = useState(null);
  const [sectionError, setSectionError] = useState("");
  const [showLockRequirements, setShowLockRequirements] = useState(false);

  useEffect(() => {
    let isCurrent = true;
    setLoading(true);
    setError("");
    setExperiment(null);
    experimentsApi.get(slug)
      .then((data) => { if (isCurrent) setExperiment(data); })
      .catch(() => {
        if (isCurrent) setError("Experiment not found or you don't have access.");
      })
      .finally(() => {
        if (isCurrent) setLoading(false);
      });
    return () => { isCurrent = false; };
  }, [slug]);

  // Re-fetch authoritative state after quizzes/code submissions. The UI does not
  // derive completion from a click or from a local optimistic flag.
  async function refreshExperiment() {
    try {
      const freshExperiment = await experimentsApi.get(slug);
      setExperiment(freshExperiment);
      return freshExperiment;
    } catch {
      // Keep the last known saved state; do not invent a new completion state.
      return null;
    }
  }

  async function markSectionCompleted(sectionKey) {
    if (!isStudent || !sectionKey || savingSection) return;
    setSavingSection(sectionKey);
    setSectionError("");
    try {
      // First persist completion through the backend. No tick is set here.
      await experimentsApi.markSectionCompleted(slug, sectionKey);
    } catch {
      setSectionError("We couldn't save this section as completed. No new completion tick was added. Please try again.");
      setSavingSection(null);
      return;
    }

    try {
      // Then fetch the database-backed status and render only that response.
      const freshExperiment = await experimentsApi.get(slug);
      setExperiment(freshExperiment);
      setShowLockRequirements(false);
    } catch {
      setSectionError("The completion request succeeded, but the saved status could not be refreshed. No new tick was added locally. Please retry or reload the experiment.");
    } finally {
      setSavingSection(null);
    }
  }

  function handleSectionSelect(section) {
    setSectionError("");
    if (section.id === "assignment" && isStudent && experiment?.assignment_locked) {
      // Show the backend-provided prerequisites only after the student clicks.
      setShowLockRequirements(true);
      setActiveSection("assignment");
      return;
    }
    setShowLockRequirements(false);
    setActiveSection(section.id);
  }

  if (loading) return <div className="page-loading">Loading experiment…</div>;
  if (error || !experiment) {
    return (
      <div className="exp-page exp-page--error">
        <div className="alert alert--error">{error || "Experiment not found."}</div>
      </div>
    );
  }

  const getQuiz = (type) => experiment.quizzes?.find((q) => q.quiz_type === type);
  const preQuiz = getQuiz("pre");
  const postQuiz = getQuiz("post");
  const assignment = getQuiz("assignment");
  const completions = experiment.section_completions || {};

  const completionControl = (sectionKey) => isStudent ? (
    <div className="section-completion">
      <button
        type="button"
        className={`btn ${completions[sectionKey] ? "btn--ghost" : "btn--primary"} section-completion__button`}
        disabled={Boolean(savingSection) || Boolean(completions[sectionKey])}
        onClick={() => markSectionCompleted(sectionKey)}
      >
        {savingSection === sectionKey ? "Saving…" : completions[sectionKey] ? "✓ Completed" : "Mark Completed"}
      </button>
      {completions[sectionKey] && <span className="section-completion__status">Saved completion confirmed</span>}
    </div>
  ) : null;

  return (
    <div className="exp-page">
      <div className="exp-page__header">
        <h1 className="exp-page__title">{experiment.title}</h1>
      </div>

      {/* Temporary tab navigation; the approved contextual left sidebar is the next UI phase. */}
      <nav className="exp-page__tabs" aria-label="Experiment sections">
        {SECTIONS.map((section) => {
          const locked = section.id === "assignment" && isStudent && experiment.assignment_locked;
          const complete = section.completionKey && completions[section.completionKey];
          return (
            <button
              key={section.id}
              type="button"
              className={`exp-tab ${activeSection === section.id ? "exp-tab--active" : ""} ${locked ? "exp-tab--locked" : ""}`}
              onClick={() => handleSectionSelect(section)}
              title={locked ? "Click to see what remains before the assignment unlocks" : undefined}
            >
              {complete ? "✓ " : locked ? "🔒 " : ""}{section.label}
            </button>
          );
        })}
      </nav>

      {sectionError && <div className="alert alert--error section-completion__error" role="alert">{sectionError}</div>}

      {showLockRequirements && experiment.assignment_locked && (
        <div className="alert alert--warning exp-page__lock-note" role="status">
          <strong>Assignment locked.</strong> Complete the following sections first:
          <ul>
            {(experiment.assignment_missing_steps || []).map((step) => <li key={step}>{step}</li>)}
          </ul>
        </div>
      )}

      <div className="exp-page__content">
        {activeSection === "overview" && (
          <section className="exp-section">
            <h2 className="exp-section__heading">{experiment.title} — Overview</h2>
            <p>{experiment.overview || `This experiment introduces the main concepts and practical workflow of ${experiment.title}.`}</p>
            {completionControl("overview")}
          </section>
        )}

        {activeSection === "aim" && (
          <section className="exp-section">
            <h2 className="exp-section__heading">Aim / Learning Objectives</h2>
            <h3>Aim</h3>
            <p>{experiment.aim}</p>
            <h3>Learning Objectives</h3>
            <p>{experiment.objective}</p>
            {completionControl("aim-objectives")}
          </section>
        )}

        {activeSection === "pre-quiz" && (
          <section className="exp-section">
            <h2 className="exp-section__heading">Pre-Quiz</h2>
            {preQuiz ? (
              <QuizPanel quiz={preQuiz} quizType="pre" onComplete={refreshExperiment} readOnly={!isStudent} />
            ) : (
              <p className="exp-section__placeholder">No pre-quiz available for this experiment yet.</p>
            )}
          </section>
        )}

        {activeSection === "video" && (
          <section className="exp-section">
            <h2 className="exp-section__heading">Video</h2>
            {experiment.video_url ? (
              <div className="exp-video-wrapper">
                <iframe
                  src={toEmbedUrl(experiment.video_url)}
                  title="Experiment video"
                  allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                  allowFullScreen
                  className="exp-video"
                />
              </div>
            ) : (
              <p className="exp-section__placeholder">No video available for this experiment yet.</p>
            )}
            {completionControl("video")}
          </section>
        )}

        {activeSection === "theory" && (
          <section className="exp-section">
            <h2 className="exp-section__heading">Theory / Reading Material</h2>
            {experiment.notes ? (
              <div className="exp-notes" dangerouslySetInnerHTML={{ __html: simpleMarkdown(experiment.notes) }} />
            ) : (
              <p className="exp-section__placeholder">No theory material available for this experiment yet.</p>
            )}
            <p className="exp-section__intro">References and supplementary reading, when available, are included at the end of this section.</p>
            {completionControl("theory")}
          </section>
        )}

        {activeSection === "guided-lab" && (
          <section className="exp-section">
            <h2 className="exp-section__heading">Guided Lab</h2>
            <p className="exp-section__intro">Explore the visual demonstration and adjust its parameters where available.</p>
            <GuidedLab labConfig={experiment.lab_config} />
            {completionControl("guided-lab")}
          </section>
        )}

        {activeSection === "code-editor" && (
          <section className="exp-section">
            <h2 className="exp-section__heading">Code Exercise</h2>
            <p className="exp-section__intro">Write and run Python code in your browser, then submit the output for validation. This section is complete only after a matching result has been saved.</p>
            <CodeEditor experiment={experiment} onSubmitted={refreshExperiment} canSubmit={isStudent} />
          </section>
        )}

        {activeSection === "post-quiz" && (
          <section className="exp-section">
            <h2 className="exp-section__heading">Post-Quiz</h2>
            {postQuiz ? (
              <QuizPanel quiz={postQuiz} quizType="post" onComplete={refreshExperiment} readOnly={!isStudent} />
            ) : (
              <p className="exp-section__placeholder">No post-quiz available for this experiment yet.</p>
            )}
          </section>
        )}

        {activeSection === "assignment" && !experiment.assignment_locked && (
          <section className="exp-section">
            <h2 className="exp-section__heading">Assignment</h2>
            {assignment ? (
              <QuizPanel quiz={assignment} quizType="assignment" onComplete={refreshExperiment} readOnly={!isStudent} />
            ) : (
              <p className="exp-section__placeholder">No assignment available for this experiment yet.</p>
            )}
          </section>
        )}
      </div>
    </div>
  );
}

function toEmbedUrl(url) {
  try {
    const u = new URL(url);
    if (u.hostname.includes("youtube.com")) {
      const videoId = u.searchParams.get("v");
      if (videoId) return `https://www.youtube.com/embed/${videoId}`;
    }
    if (u.hostname === "youtu.be") return `https://www.youtube.com/embed${u.pathname}`;
  } catch { /* use the supplied URL as a fallback */ }
  return url;
}

function simpleMarkdown(text) {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/^### (.+)$/gm, "<h3>$1</h3>")
    .replace(/^## (.+)$/gm, "<h2>$1</h2>")
    .replace(/^# (.+)$/gm, "<h1>$1</h1>")
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/\*(.+?)\*/g, "<em>$1</em>")
    .replace(/`(.+?)`/g, "<code>$1</code>")
    .replace(/\n/g, "<br>");
}
