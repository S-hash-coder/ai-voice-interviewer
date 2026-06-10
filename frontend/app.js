let sessionId = null;
let questionCount = 0;

const chatBox = document.getElementById("chat");
const statusDiv = document.getElementById("status");

let isProcessing = false;
let interviewStarted = false;

// --------------------
// SPEECH RECOGNITION
// --------------------
const SpeechRecognition =
    window.SpeechRecognition || window.webkitSpeechRecognition;

const recognition = new SpeechRecognition();

recognition.continuous = false;
recognition.interimResults = false;
recognition.lang = "en-US";


// --------------------
// UI HELPERS
// --------------------
function addMessage(text, type) {
    const msg = document.createElement("div");
    msg.classList.add("message", type);
    msg.innerText = text;

    chatBox.appendChild(msg);
    chatBox.scrollTop = chatBox.scrollHeight;
}

function setStatus(text) {
    statusDiv.innerText = text;
}


// --------------------
// UPLOAD RESUME
// --------------------
async function uploadResume(file) {

    setStatus("Uploading resume...");

    const formData = new FormData();
    formData.append("file", file);

    const res = await fetch("http://127.0.0.1:8001/upload", {
        method: "POST",
        body: formData
    });

    const data = await res.json();

    sessionId = data.session_id;

    console.log("SESSION ID:", sessionId);

    setStatus("Resume uploaded ✔ Ready to start interview");
}


// --------------------
// START INTERVIEW
// --------------------
async function startInterview() {

    if (!sessionId) {
        setStatus("⚠ Upload resume first");
        return;
    }

    setStatus("Starting interview...");

    try {
        const res = await fetch(
            `http://127.0.0.1:8001/start?session_id=${sessionId}`
        );

        const data = await res.json();

        if (!data.question) {
            setStatus("Server error / LLM busy");
            return;
        }

        interviewStarted = true;
        questionCount++;

        addMessage(`Q${questionCount}: ${data.question}`, "bot");
        speak(data.question);

    } catch (err) {
        console.error(err);
        setStatus("Backend error");
    }
}


// --------------------
// TEXT TO SPEECH
// --------------------
function speak(text) {
    const speech = new SpeechSynthesisUtterance(text);

    speech.onstart = () => {
        setStatus("AI is speaking...");
    };

    speech.onend = () => {
        setStatus("Listening...");

        isProcessing = false;

        if (interviewStarted) {
            setTimeout(() => {
                try {
                    recognition.start();
                } catch (e) {
                    console.log("recognition already running");
                }
            }, 700);
        }
    };

    window.speechSynthesis.speak(speech);
}


// --------------------
// SPEECH TO TEXT
// --------------------
recognition.onresult = async (event) => {

    if (!interviewStarted || isProcessing) return;

    const answer = event.results[0][0].transcript;

    if (!answer || answer.trim() === "") return;

    isProcessing = true;

    addMessage(answer, "user");
    setStatus("Thinking...");

    try {
        const res = await fetch(
            `http://127.0.0.1:8001/chat?answer=${encodeURIComponent(answer)}&session_id=${sessionId}`
        );

        const data = await res.json();

        if (!data.question) {
            setStatus("LLM busy. Try again...");
            isProcessing = false;
            return;
        }

        questionCount++;

        addMessage(`Q${questionCount}: ${data.question}`, "bot");
        speak(data.question);

    } catch (err) {
        console.error(err);
        setStatus("Backend error");
        isProcessing = false;
    }
};


// --------------------
// STOP INTERVIEW
// --------------------
function stopInterview() {
    interviewStarted = false;
    isProcessing = false;
    questionCount = 0;

    try {
        recognition.stop();
    } catch (e) {}

    window.speechSynthesis.cancel();

    setStatus("Stopped");
}


// --------------------
// ERROR HANDLING
// --------------------
recognition.onerror = () => {
    isProcessing = false;

    setTimeout(() => {
        if (interviewStarted) {
            try {
                recognition.start();
            } catch (e) {
                console.log("retry handled");
            }
        }
    }, 1000);
};