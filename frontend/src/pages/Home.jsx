import { useAuth } from "../context/AuthContext.jsx";
import { homeIntro, homeTopics } from "../content/homeContent.js";
import { instructorHomeIntro, instructorHomeTopics } from "../content/instructorHomeContent.js";
import "./Home.css";

// Home shows general content only. Students see general Machine Learning content;
// instructors see content about the Virtual Lab. Experiment access lives on the
// Experiments page and progress lives on View Progress.
export default function Home() {
  const { user } = useAuth();
  const isInstructor = user?.role === "instructor";
  const intro = isInstructor ? instructorHomeIntro : homeIntro;
  const topics = isInstructor ? instructorHomeTopics : homeTopics;

  return (
    <div className="home">
      <div className="home__hero">
        <h1 className="home__title">{intro.title}</h1>
        <p className="home__subtitle">{intro.subtitle}</p>
        <p className="home__greeting">Welcome, {user?.full_name}</p>
      </div>

      <div className="home__topics">
        {topics.map((topic) => (
          <section key={topic.title} className="home__topic">
            <h2 className="home__topic-title">{topic.title}</h2>
            <p className="home__topic-body">{topic.body}</p>
          </section>
        ))}
      </div>
    </div>
  );
}
