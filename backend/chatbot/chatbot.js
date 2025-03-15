
const chatbot = async (req, res) => {
    try {
        const { text } = req.body

        const result = await hf.textClassification({
            model: "distilbert-base-uncased-finetuned-sst-2-english",
            inputs: text,
        })

        const label = result[0].label
        const score = result[0].score
    }
    catch (error) {
        res.status({error: error.message})
    }
}

module.exports = { chatbot }