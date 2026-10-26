"""Canonical keys and database helpers for required manual sections.

Keep this list aligned with the student experiment workspace. The Code Exercise is
tracked here too (Mark Completed); a matched submission does not complete it.
Quizzes and the assignment deliberately do not belong here.
"""

import uuid

from sqlalchemy.orm import Session

from app.models.section_completion import SectionCompletion


STATIC_SECTION_LABELS: dict[str, str] = {
    "overview": "Experiment Title / Overview",
    "aim-objectives": "Aim / Learning Objectives",
    "theory": "Theory / Reading Material",
    "video": "Video",
    "guided-lab": "Guided Lab",
    "code-exercise": "Code Exercise",
}


def get_section_completion_map(
    student_id: uuid.UUID, experiment_id: uuid.UUID, db: Session
) -> dict[str, bool]:
    """Return every supported manual section key, with status from saved DB rows."""
    completed_keys = {
        row.section_key
        for row in db.query(SectionCompletion.section_key).filter(
            SectionCompletion.student_id == student_id,
            SectionCompletion.experiment_id == experiment_id,
        ).all()
    }
    return {key: key in completed_keys for key in STATIC_SECTION_LABELS}


def get_completed_section_keys(
    student_id: uuid.UUID, experiment_id: uuid.UUID, db: Session
) -> set[str]:
    """Return manually completed section keys for prerequisite/progress calculations."""
    return {
        row.section_key
        for row in db.query(SectionCompletion.section_key).filter(
            SectionCompletion.student_id == student_id,
            SectionCompletion.experiment_id == experiment_id,
        ).all()
    }
