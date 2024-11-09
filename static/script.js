document.getElementById("generate-form").addEventListener("submit", async (event) => {
    event.preventDefault();

    const formData = new FormData(event.target);
    const response = await fetch("/generate", {
        method: "POST",
        body: formData
    });

    const data = await response.json();
    document.getElementById("generated_text").innerText = data.generated_text || data.error;
});

async function sendTranscript() {
    const transcript = document.getElementById("transcript").value;

    const response = await fetch("/receive_transcript", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ text: transcript })
    });

    const data = await response.json();
    if (data.success) {
        alert("Transcript received: " + data.transcript);
    } else {
        alert("Failed to send transcript.");
    }
}
