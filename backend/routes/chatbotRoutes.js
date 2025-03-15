const express = require('express')

const chatbot = require('../chatbot/chatbot')

const router = express.Router()

router.post('/', chatbot)

module.exports = router