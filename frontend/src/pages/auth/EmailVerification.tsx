import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card'

export default function EmailVerification() {
  const [code, setCode] = useState(['', '', '', '', '', ''])
  const navigate = useNavigate()

  const handleChange = (index: number, value: string) => {
    if (value.length > 1) return
    const newCode = [...code]
    newCode[index] = value
    setCode(newCode)
    
    // Auto-focus next input
    if (value && index < 5) {
      const nextInput = document.getElementById(`code-${index + 1}`)
      nextInput?.focus()
    }
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    // Placeholder - will connect to backend later
    console.log('Verify code:', code.join(''))
    navigate('/dashboard')
  }

  return (
    <div className="animate-fade-in">
      <Card>
        <CardHeader className="text-center">
          <CardTitle className="text-headline-md">Verify your email</CardTitle>
          <CardDescription>
            Enter the 6-digit code sent to your email.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="flex gap-2 justify-center">
              {code.map((digit, index) => (
                <Input
                  key={index}
                  id={`code-${index}`}
                  type="text"
                  maxLength={1}
                  value={digit}
                  onChange={(e) => handleChange(index, e.target.value)}
                  className="w-12 h-12 text-center text-headline-md font-mono-data"
                />
              ))}
            </div>
            <Button type="submit" className="w-full">
              Verify Email
            </Button>
            <Button type="button" variant="ghost" className="w-full">
              Resend Code
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}
