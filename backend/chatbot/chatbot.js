const chatbot = async (req, res) => {
    try {
        const { message } = req.body

        // Make API call to Python backend
        const response = await fetch('http://localhost:5000/analyze', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ message })
        })

        // Check if the response is ok (status in the range 200-299)
        if (!response.ok) {
            const errorData = await response.text()
            console.error(`Python API error: ${response.status} - ${errorData}`)
            return res.status(response.status).json({ 
                error: `AI server error: ${response.status}`,
                details: errorData
            })
        }

        // Parse the successful response
        const data = await response.json()
        console.log("Chatbot API Working")
        res.status(200).json(data)
    } 
    catch (error) {
        console.error("Chatbot controller error:", error)
        
        // This catches network errors like when the Python server is down
        res.status(500).json({ 
            error: "Cannot connect to AI server",
            details: error.message
        })
    }
}

module.exports = chatbot