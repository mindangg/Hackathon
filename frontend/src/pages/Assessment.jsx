import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import "../styles/Assessment.css"
const questions = [
  {
    id: 1,
    type: "options",
    text:"How are you feel today?",
    options: ["Sad", "Stressed", "Neutral", "Happy"]
  },
  {
    id: 2,
    type: "options",
    text: "How often do you exercise?",
    options: ["Rarely", "1-2 times a week", "3-5 times a week", "Daily"],
  },
  {
    id: 3,
    type: "options",
    text: "How many hours do you sleep per night?",
    options: ["Less than 5", "5-6", "7-8", "More than 8"],
  },
  {
    id: 4,
    text: "How would you rate your diet?",
    options: ["Poor", "Average", "Good", "Excellent"],
  },
  {
    id: 5,
    text: "Do you smoke or drink alcohol regularly?",
    options: ["No", "Rarely", "Sometimes", "Always"],
    
  },
  {
    id: 6,
    text: "How (caan nang)"
  },
  
  {
    id: 7,
    text:"Do you often wake up feeling tired or low energy?",
    options:["Yes", "No"]
  },
  {
    id: 8,
    text:"What is the biggest source of stress for you right now?",
    options: ["Work", "Studies", "Relationships","Finances","Other"]
  },
  {
    id: 9,
    type: "text",
    text:"How would you describe your overall health status?",
  },
];

export default function Assessment() {
  const [currentQuestion, setCurrentQuestion] = useState(0);
  const [answers, setAnswers] = useState({});
  const navigate = useNavigate();

  const handleAnswer = (id, value) => {
    setAnswers((prev) => ({ ...prev, [id]: value }));
    
    // Nếu chưa phải câu cuối, tự động chuyển sang câu tiếp theo
    if (currentQuestion < questions.length - 1) {
      setTimeout(() => setCurrentQuestion((prev) => prev + 1), 300); // Thêm độ trễ nhỏ để người dùng thấy hiệu ứng chọn
    } else {
      submitAssessment(); // Nếu là câu cuối, gửi kết quả
    }
  };
  

  const nextQuestion = () => {
    if (currentQuestion < questions.length - 1) {
      setCurrentQuestion(currentQuestion + 1);
    }
  };

  const prevQuestion = () => {
    if (currentQuestion > 0) {
      setCurrentQuestion(currentQuestion - 1);
    }
  };

  const submitAssessment = () => {
    console.log("User's answers:", answers);
    navigate("/results");
  };

  return (
    <div className="assessment-container">
      <h2>Health Assessment</h2>
      <p>{questions[currentQuestion].text}</p>

      {questions[currentQuestion].type === "options" ? (
        <div className="options">
          {questions[currentQuestion].options.map((option, index) => (
            <label key={index} className="option-label">
              <input 
                type="radio"
                name={`question-${currentQuestion}`}
                value={option}
                checked={answers[questions[currentQuestion].id] === option}
                onChange={() => handleAnswer(questions[currentQuestion].id, option)}
              />
              <div className="option-box">{option}</div>
            </label>
          ))}
        </div>
      ) : (
          <input
          type="text"
          placeholder="Type Your Answer here"
          value={answers[questions[currentQuestion].id] || ""}
          onChange={(e) => handleAnswer(questions[currentQuestion].id, e.target.value)}
          className="text-input"
          />
      )}
      {/* <div>
      <button id="prev" onClick={prevQuestion} disabled={currentQuestion === 0}>
          Previous
        </button>
        {currentQuestion < questions.length - 1 ? (
          <button id="next" onClick={nextQuestion}>Next</button>
        ) : (
          <button onClick={submitAssessment}>Submit</button>
        )}
      </div> */}
    </div>
  );
}

