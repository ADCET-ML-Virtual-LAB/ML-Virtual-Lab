import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { instructorApi } from "../api/instructor.js";
import AnswerKey from "../components/AnswerKey.jsx";
import { SECTION_LABELS } from "../constants/sections.js";
import { simpleMarkdown, toEmbedUrl } from "../utils/contentFormat.js";
import "./InstructorConsole.css";

// Read-only experiment content: the student sections without Guided Lab and
// Code Exercise, in the same order. Quizzes show their answer keys.
const TABS = [
  { id: "overview", label: SECTION_LABELS.overview },
  { id: "aim", label: SECTION_LABELS["aim-objectives"] },
  { id: "pre-quiz", label: SECTION_LABELS["pre-quiz"] },
  { id: "video", label: SECTION_LABELS.video },
  { id: "theory", label: SECTION_LABELS.theory },
  { id: "post-quiz", label: SECTION_LABELS["post-quiz"] },
  { id: "assignment", label: SECTION_LABELS.assignment },
];

export default function InstructorExperiment() {
  const { batchId, experimentId } = useParams();
  const [experiment, setExperiment] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [tab, setTab] = useState("overview");
  const [reloadKey, setReloadKey] = useState(0);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError("");
    setExperiment(null);
    setTab("overview");
    instructorApi
      .experiment(experimentId)
      .then((data) => !cancelled && setExperiment(data))
      .catch((err) => {
        if (cancelled) return;
        setError(
          err.response?.status === 404
            ? "This experiment is not available."
            : "Could not load this experiment. Please try again."
        );
      })
      .finally(() => !cancelled && setLoading(false));
    return () => {
      cancelled = true;
    };
  }, [experimentId, reloadKey]);

  if (loading) return <div className="page-loading">Loading experiment…</div>;

  if (error || !experiment) {
    return (
      <div className="alert alert--error ic-alert">
        <span>{error || "Experiment not found."}</span>
        <button type="button" className="btn btn--sm btn--ghost" onClick={() => setReloadKey((k) => k + 1)}>
          Retry
        </button>
      </div>
    );
  }

  return (
    <div>
      <div className="ic-header">
        <h1 className="ic-page__title">
          Experiment {experiment.number}: {experiment.title}
        </h1>
        <Link to={`/batches/${batchId}/experiments/${experimentId}/status`} className="btn btn--primary btn--sm">
          Students Status
        </Link>
      </div>

      <div className="ic-tabs" role="tablist">
        {TABS.map((t) => (
          <button
            key={t.id}
            type="button"
            role="tab"
            aria-selected={tab === t.id}
            className={`ic-tab${tab === t.id ? " ic-tab--active" : ""}`}
            onClick={() => setTab(t.id)}
          >
            {t.label}
          </button>
        ))}
      </div>

      <section className="card ic-section">
        {tab === "overview" && (
          <>
            <h2 className="ic-section__heading">{experiment.title} — Overview</h2>
            <p>
              {experiment.overview ||
                `This experiment introduces the main concepts and practical workflow of ${experiment.title}.`}
            </p>
          </>
        )}

        {tab === "aim" && (
          <>
            <h2 className="ic-section__heading">{SECTION_LABELS["aim-objectives"]}</h2>
            <h3>Aim</h3>
            <p>{experiment.aim}</p>
            <h3>Learning Objectives</h3>
            <p>{experiment.objective}</p>
          </>
        )}

        {tab === "pre-quiz" && (
          <>
            <h2 className="ic-section__heading">{SECTION_LABELS["pre-quiz"]}</h2>
            <AnswerKey quiz={experiment.pre_quiz} emptyText="No pre-quiz available for this experiment yet." />
          </>
        )}

        {tab === "video" && (
          <>
            <h2 className="ic-section__heading">{SECTION_LABELS.video}</h2>
            {experiment.video_url ? (
              <div className="ic-video">
                <iframe
                  src={toEmbedUrl(experiment.video_url)}
                  title="Experiment video"
                  allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                  allowFullScreen
                />
              </div>
            ) : (
              <p className="ic-placeholder">No video available for this experiment yet.</p>
            )}
          </>
        )}

        {tab === "theory" && (
          <>
            <h2 className="ic-section__heading">{SECTION_LABELS.theory}</h2>
            {experiment.notes ? (
              <div className="ic-notes" dangerouslySetInnerHTML={{ __html: simpleMarkdown(experiment.notes) }} />
            ) : (
              <p className="ic-placeholder">No theory material available for this experiment yet.</p>
            )}
          </>
        )}

        {tab === "post-quiz" && (
          <>
            <h2 className="ic-section__heading">{SECTION_LABELS["post-quiz"]}</h2>
            <AnswerKey quiz={experiment.post_quiz} emptyText="No post-quiz available for this experiment yet." />
          </>
        )}

        {tab === "assignment" && (
          <>
            <h2 className="ic-section__heading">{SECTION_LABELS.assignment}</h2>
            <AnswerKey quiz={experiment.assignment} emptyText="No assignment available for this experiment yet." />
          </>
        )}
      </section>
    </div>
  );
}
