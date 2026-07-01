import { Search } from 'lucide-react'
import { Input } from '@/components/ui/input'
import { cn } from '@/lib/utils'

interface SearchBarProps {
  value?: string
  onChange?: (value: string) => void
  onSubmit?: (value: string) => void
  placeholder?: string
  className?: string
}

export default function SearchBar({
  value,
  onChange,
  onSubmit,
  placeholder = 'Search...',
  className,
}: SearchBarProps) {
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (onSubmit && value) {
      onSubmit(value)
    }
  }

  return (
    <form onSubmit={handleSubmit} className={cn('relative', className)}>
      <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 h-5 w-5 text-outline" />
      <Input
        type="search"
        placeholder={placeholder}
        value={value}
        onChange={(e) => onChange?.(e.target.value)}
        className="pl-12 pr-4 h-14 text-body-lg"
      />
      <div className="absolute right-4 top-1/2 transform -translate-y-1/2">
        <kbd className="px-2 py-1 text-label-caps bg-surface-container-high rounded border border-outline">
          ⌘K
        </kbd>
      </div>
    </form>
  )
}
