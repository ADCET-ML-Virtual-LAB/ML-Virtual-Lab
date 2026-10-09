import { useState, useEffect } from "react";
import { useParams } from "react-router-dom";
import { experimentsApi } from "../api/experiments.js";
import QuizPanel from "../components/QuizPanel.jsx";
import GuidedLab from "../components/GuidedLab.jsx";
import CodeEditor from "../components/CodeEditor.jsx";
import "./ExperimentPage.css";

const SECTIONS = [
  { id: "aim", label: "Aim & Objective" },
  { id: "pre-quiz", label: "Pre-Quiz" },
  { id: "video", label: "Video" },
  { id: "notes", label: "Theory Notes" },
  { id: "guided-lab", label: "Guided Lab" },
  { id: "code-editor", label: "Code Exercise" },
  { id: "post-quiz", label: "Post-Quiz" },
  { id: "assignment", label: "Assignment" },
];

export default function ExperimentPage() {
  const { slug } = useParams();
  const [experiment, setExperiment] = useState(null);
  const [activeSection, setActiveSection] = useState("aim");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    setLoading(true);
    experimentsApi
      .get(slug)
      .then(setExperiment)
      .catch(() => setError("Experiment not found or you don't have access."))
      .finally(() => setLoading(false));
  }, [slug]);

  if (loading) return <div className="page-loading">Loading experiment…</div>;
  if (error || !experiment) {
    return (
      <div className="exp-page exp-page--error">
        <div className="alert alert--error">{error || "Experiment not found."}</div>
      </div>
    );
  }

  // Get quizzes by type
  const getQuiz = (type) => experiment.quizzes?.find((q) => q.quiz_type === type);

  const preQuiz = getQuiz("pre");
  const postQuiz = getQuiz("post");
  const assignment = getQuiz("assignment");

  return (
    <div className="exp-page">
      <div className="exp-page__header">
        <h1 className="exp-page__title">{experiment.title}</h1>
      </div>

      {/* Section tabs */}
      <nav className="exp-page__tabs">
        {SECTIONS.map((s) => (
          <button
            key={s.id}
            className={`exp-tab ${activeSection === s.id ? "exp-tab--active" : ""}`}
            onClick={() => setActiveSection(s.id)}
          >
            {s.label}
          </button>
        ))}
      </nav>

      <div className="exp-page__content">

        {/* ── Aim & Objective ── */}
        {activeSection === "aim" && (
          <section className="exp-section">
            <h2 className="exp-section__heading">Aim</h2>
            <p>{experiment.aim}</p>
            <h2 className="exp-section__heading">Objective</h2>
            <p>{experiment.objective}</p>
          </section>
        )}

        {/* ── Pre-Quiz ── */}
        {activeSection === "pre-quiz" && (
          <section className="exp-section">
            <h2 className="exp-section__heading">Pre-Quiz</h2>
            {preQuiz ? (
              <QuizPanel quiz={preQuiz} quizType="pre" />
            ) : (
              <p className="exp-section__placeholder">No pre-quiz available for this experiment yet.</p>
            )}
          </section>
        )}

        {/* ── Video ── */}
        {activeSection === "video" && (
          <section className="exp-section">
            <h2 className="exp-section__heading">Video Lecture</h2>
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
              <p className="exp-section__placeholder">No video available for this experiment.</p>
            )}
          </section>
        )}

        {/* ── Theory Notes ── */}
        {activeSection === "notes" && (
          <section className="exp-section">
            <h2 className="exp-section__heading">Theory Notes</h2>
            {experiment.notes ? (
              <div
                className="exp-notes"
                dangerouslySetInnerHTML={{ __html: simpleMarkdown(experiment.notes) }}
              />
            ) : (
              <p className="exp-section__placeholder">No notes available for this experiment.</p>
            )}
          </section>
        )}

        {/* ── Guided Lab ── */}
        {activeSection === "guided-lab" && (
          <section className="exp-section">
            <h2 className="exp-section__heading">Guided / Parametric Lab</h2>
            <p className="exp-section__intro">
              Adjust the parameters below and click <strong>Run Lab</strong> to see how the
              algorithm responds. This is fully interactive — nothing is sent to the server.
            </p>
            <GuidedLab labConfig={experiment.lab_config} />
          </section>
        )}

        {/* ── Code Exercise ── */}
        {activeSection === "code-editor" && (
          <section className="exp-section">
            <h2 className="exp-section__heading">Code Exercise</h2>
            <p className="exp-section__intro">
              Write your Python code below. Click <strong>▶ Run</strong> to execute it in your
              browser (via Pyodide), then <strong>Submit for feedback</strong> to see how your
              output compares to the expected result.
            </p>
            <CodeEditor experiment={experiment} />
          </section>
        )}

        {/* ── Post-Quiz ── */}
        {activeSection === "post-quiz" && (
          <section className="exp-section">
            <h2 className="exp-section__heading">Post-Quiz</h2>
            {postQuiz ? (
              <QuizPanel quiz={postQuiz} quizType="post" />
            ) : (
              <p className="exp-section__placeholder">No post-quiz available for this experiment yet.</p>
            )}
          </section>
        )}

        {/* ── Assignment ── */}
        {activeSection === "assignment" && (
          <section className="exp-section">
            <h2 className="exp-section__heading">Assignment</h2>
            {assignment ? (
              <QuizPanel quiz={assignment} quizType="assignment" />
            ) : (
              <p className="exp-section__placeholder">No assignment available for this experiment yet.</p>
            )}
          </section>
        )}

      </div>
    </div>
  );
}

/** Convert YouTube watch URL to embed URL */
function toEmbedUrl(url) {
  try {
    const u = new URL(url);
    if (u.hostname.includes("youtube.com")) {
      const v = u.searchParams.get("v");
      if (v) return `https://www.youtube.com/embed/${v}`;
    }
    if (u.hostname === "youtu.be") {
      return `https://www.youtube.com/embed${u.pathname}`;
    }
  } catch {}
  return url; // fallback — use as-is (handles embed URLs already)
}

/** Minimal markdown renderer for theory notes (headers, bold, code) */
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
