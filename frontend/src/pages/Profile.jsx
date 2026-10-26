import { useAuth } from "../context/AuthContext.jsx";
import "./Profile.css";

const ROLE_LABEL = { student: "Student", instructor: "Instructor", admin: "Admin" };

// Read-only account details. The final field list and any editable fields or
// account actions are still to be decided.
export default function Profile() {
  const { user } = useAuth();
  if (!user) return null;

  const rows = [
    ["Name", user.full_name],
    ["Email", user.email],
    ...(user.role === "student" ? [["Roll No. / URN", user.roll_number || "—"]] : []),
    ["Role", ROLE_LABEL[user.role] || user.role],
  ];

  return (
    <div className="profile">
      <h1 className="profile__title">My Profile</h1>
      <dl className="profile__card">
        {rows.map(([label, value]) => (
          <div key={label} className="profile__row">
            <dt className="profile__label">{label}</dt>
            <dd className="profile__value">{value}</dd>
          </div>
        ))}
      </dl>
    </div>
  );
}
