import { useState } from 'react'
import SearchBar from '@/components/features/search-bar'
import CitationCard from '@/components/features/citation-card'
import EmptyState from '@/components/features/empty-state'
import ErrorState from '@/components/features/error-state'
import { Skeleton } from '@/components/ui/skeleton'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { useHybridSearch, useSearchStats } from '@/hooks/useSearch'
import { useSearchStore } from '@/stores/search-store'
import { Search as SearchIcon, Sliders } from 'lucide-react'

export default function Search() {
  const [query, setQuery] = useState('')
  const [showFilters, setShowFilters] = useState(false)
  const [topK, setTopK] = useState(10)
  const [vectorWeight, setVectorWeight] = useState(0.7)
  const [bm25Weight, setBm25Weight] = useState(0.3)
  
  const { results, isSearching } = useSearchStore()
  const hybridSearch = useHybridSearch()
  const { data: stats } = useSearchStats()

  const handleSearch = (searchQuery: string) => {
    if (!searchQuery.trim()) return
    
    hybridSearch.mutate({
      query: searchQuery,
      top_k: topK,
      vector_weight: vectorWeight,
      bm25_weight: bm25Weight
    })
  }

  return (
    <div className="space-y-lg">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-display-lg-mobile font-bold text-foreground">Knowledge Search</h1>
          <p className="text-body-md text-muted-foreground mt-2">
            Search across {stats?.total_documents?.toLocaleString() || '...'} medical documents
          </p>
        </div>
        <Button
          variant="outline"
          onClick={() => setShowFilters(!showFilters)}
        >
          <Sliders className="mr-2 h-4 w-4" />
          Filters
        </Button>
      </div>

      <SearchBar
        value={query}
        onChange={setQuery}
        onSubmit={handleSearch}
        placeholder="Search for medical information..."
      />

      {/* Filters */}
      {showFilters && (
        <Card>
          <CardContent className="pt-lg space-y-4">
            <div>
              <label className="text-body-sm font-medium text-foreground">
                Results: {topK}
              </label>
              <input
                type="range"
                min="1"
                max="20"
                value={topK}
                onChange={(e) => setTopK(Number(e.target.value))}
                className="w-full mt-2"
              />
            </div>
            <div>
              <label className="text-body-sm font-medium text-foreground">
                Vector Weight: {vectorWeight.toFixed(2)}
              </label>
              <input
                type="range"
                min="0"
                max="1"
                step="0.1"
                value={vectorWeight}
                onChange={(e) => {
                  const val = Number(e.target.value)
                  setVectorWeight(val)
                  setBm25Weight(1 - val)
                }}
                className="w-full mt-2"
              />
            </div>
            <div>
              <label className="text-body-sm font-medium text-foreground">
                BM25 Weight: {bm25Weight.toFixed(2)}
              </label>
              <input
                type="range"
                min="0"
                max="1"
                step="0.1"
                value={bm25Weight}
                onChange={(e) => {
                  const val = Number(e.target.value)
                  setBm25Weight(val)
                  setVectorWeight(1 - val)
                }}
                className="w-full mt-2"
              />
            </div>
          </CardContent>
        </Card>
      )}

      {/* Results */}
      <div className="space-y-lg">
        {isSearching ? (
          <>
            <Skeleton className="h-48" />
            <Skeleton className="h-48" />
            <Skeleton className="h-48" />
          </>
        ) : hybridSearch.error ? (
          <ErrorState
            title="Search failed"
            description={(hybridSearch.error as Error).message}
            onRetry={() => handleSearch(query)}
          />
        ) : results.length === 0 ? (
          <EmptyState
            icon={SearchIcon}
            title="No search results"
            description="Enter a query above to search the knowledge base."
          />
        ) : (
          <>
            <p className="text-body-sm text-muted-foreground">
              Found {results.length} results
            </p>
            {results.map((result, idx) => (
              <CitationCard
                key={idx}
                source={result.document}
                excerpt={result.content}
                similarity={result.similarity}
                metadata={result.metadata}
              />
            ))}
          </>
        )}
      </div>
    </div>
  )
}
