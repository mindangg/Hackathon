const axios = require('axios')

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
            const errorText = await response.text()
            throw new Error(`Error ${response.status}: ${errorText}`)
        }

        const data = await response.json()

        console.log("Chatbot API Working")
        res.status(200).json(data)

    } 
    catch (error) {

        if (error.response) {
            // Lỗi từ server Python (có response)
            res.status(error.response.status).json({ error: error.response.data })
        } else if (error.request) {
            // Lỗi khi không thể kết nối đến server Python
            res.status(500).json({ error: "Cannot connect to AI server" })
        } else {
            // Lỗi khác
            res.status(500).json({ error: "Internal Server Error" })
        }
    }
}

module.exports = chatbot
