import { useState } from 'react'
import { useNavigate } from 'react-router-dom'

export default function Login() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const navigate = useNavigate()

  const handleLogin = async (e) => {
    e.preventDefault()
    setIsLoading(true)
    
    try {
      // TODO: Implement actual login API call
      // For demo, just redirect after delay
      await new Promise(resolve => setTimeout(resolve, 1000))
      navigate('/dashboard')
    } catch (error) {
      console.error('Login failed:', error)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-[#0A0F1E] px-4">
      <div className="w-full max-w-md animate-slide-up">
        {/* Logo */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-white mb-2">ClearDesk</h1>
          <p className="text-[#94A3B8]">Compliance Agent for African Business</p>
        </div>

        {/* Login Form */}
        <div className="card">
          <form onSubmit={handleLogin} className="space-y-6">
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-white mb-2">
                Email Address
              </label>
              <input
                type="email"
                id="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full px-4 py-3 bg-[#0A0F1E] border border-[#2D3B4E] rounded-lg text-white placeholder-[#94A3B8] focus:outline-none focus:border-[#1A7F5A] transition-colors"
                placeholder="you@company.com"
                required
              />
            </div>

            <div>
              <label htmlFor="password" className="block text-sm font-medium text-white mb-2">
                Password
              </label>
              <input
                type="password"
                id="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full px-4 py-3 bg-[#0A0F1E] border border-[#2D3B4E] rounded-lg text-white placeholder-[#94A3B8] focus:outline-none focus:border-[#1A7F5A] transition-colors"
                placeholder="••••••••"
                required
              />
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full btn-primary py-3 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? 'Signing in...' : 'Sign In'}
            </button>
          </form>

          <div className="mt-6 text-center">
            <p className="text-sm text-[#94A3B8]">
              Don't have an account?{' '}
              <button className="text-[#1A7F5A] hover:underline font-medium">
                Contact us for access
              </button>
            </p>
          </div>
        </div>

        {/* Demo notice */}
        <div className="mt-8 text-center">
          <p className="text-xs text-[#94A3B8]">
            Demo mode: Click "Sign In" to enter the dashboard
          </p>
        </div>
      </div>
    </div>
  )
}
