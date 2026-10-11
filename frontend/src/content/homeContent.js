// Draft general Machine Learning content for the Home page.
// Edit this file to change what Home shows. No experiment progress belongs here.
export const homeIntro = {
  title: "ML Virtual Lab",
  subtitle:
    "Learn classical Machine Learning through theory, interactive labs and guided code exercises, all in your browser.",
};

export const homeTopics = [
  {
    title: "What is Machine Learning?",
    body:
      "Machine Learning is a way of building programs that learn patterns from data instead of following rules written by hand. A model is trained on examples and then used to make predictions on new data.",
  },
  {
    title: "Supervised learning",
    body:
      "The training data comes with the correct answers (labels). The model learns the link between inputs and answers, for example predicting a house price (regression) or whether an email is spam (classification).",
  },
  {
    title: "Unsupervised learning",
    body:
      "The data has no labels. The model looks for structure on its own, for example grouping similar customers together (clustering).",
  },
  {
    title: "Training and testing",
    body:
      "A model is trained on one part of the data and tested on a part it has not seen. Testing shows how well it is likely to work on new data, not just on the examples it memorised.",
  },
];
