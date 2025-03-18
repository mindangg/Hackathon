const chatbot = async (req, res) => {
    try {
        const { message } = req.body

        const response = await fetch('http://localhost:5000/analyze', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ message })
        })

        if (!response.ok) {
            const errorData = await response.text()
            console.error(`Python API error: ${response.status} - ${errorData}`)
            return res.status(response.status).json({ 
                error: `AI server error: ${response.status}`,
                details: errorData
            })
        }

  
        const data = await response.json()
        console.log("Chatbot API Working")
        res.status(200).json(data)
    } 
    catch (error) {
        console.error("Chatbot controller error:", error)
        

        res.status(500).json({ 
            error: "Cannot connect to AI server",
            details: error.message
        })
    }
}

module.exports = chatbot