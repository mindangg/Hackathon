require('dotenv').config()
const express = require('express')
const mongoose = require('mongoose')
const cors = require('cors')

const userRoutes = require('./routes/userRoutes')
const chatbotRoutes = require('./routes/chatbotRoutes')

const app = express()

// middleware
app.use(express.json())

app.use((req, res, next) => {
    console.log(req.path, req.method)
    next()
})

// cors
app.use(cors({origin: 'http://localhost:5173'}))
// app.use(cors())

// routes
app.use('/api/user', userRoutes)
app.use('/api/chatbot', chatbotRoutes)

mongoose.connect(process.env.MONGO_URI)
    .then(() => {
        app.listen(process.env.PORT, () => {
            console.log('Connected to db and listening to port', process.env.PORT)
        })
    })
    .catch((error) => {
        console.log(error)
    })

app.get('/', (req, res) => {
    res.status(200).json({mssg: 'Welcome to the app'})
})