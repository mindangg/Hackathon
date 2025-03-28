import { useState } from 'react'
import { useAuthContext } from './useAuthContext'
import { useNotificationContext } from '../hooks/useNotificationContext'

export const useLogin = () => {
    const [error, setError] = useState(null)
    const [isLoading, setIsLoading] = useState(null)
    const { dispatch } = useAuthContext()
    const { showNotification } = useNotificationContext()

    const login = async (username, password) => {
        setIsLoading(true)
        setError(null)

        const response = await fetch('http://localhost:4000/api/user/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ username, password })
        })
    
        const json = await response.json()
    
        if (!response.ok) {
            setIsLoading(false)
            setError(json.error)
        }
    
        if (response.ok) {
            // save user to local storage
            localStorage.setItem('user', JSON.stringify(json))

            // show notification login
            showNotification(`Hello ${username}`)
            
            // update the auth context
            dispatch({type: 'LOGIN', payload: json})
    
            setIsLoading(false)
        }
    }

    return { login, error, isLoading }
}