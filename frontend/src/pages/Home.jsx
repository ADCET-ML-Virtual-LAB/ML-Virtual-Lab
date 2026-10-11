import { useAuth } from "../context/AuthContext.jsx";
import { homeIntro, homeTopics } from "../content/homeContent.js";
import "./Home.css";

// Home shows general Machine Learning content only. Experiment access lives on the
// Experiments page and progress lives on View Progress.
export default function Home() {
  const { user } = useAuth();

  return (
    <div className="home">
      <div className="home__hero">
        <h1 className="home__title">{homeIntro.title}</h1>
        <p className="home__subtitle">{homeIntro.subtitle}</p>
        <p className="home__greeting">Welcome, {user?.full_name}</p>
      </div>

      <div className="home__topics">
        {homeTopics.map((topic) => (
          <section key={topic.title} className="home__topic">
            <h2 className="home__topic-title">{topic.title}</h2>
            <p className="home__topic-body">{topic.body}</p>
          </section>
        ))}
      </div>
    </div>
  );
}
