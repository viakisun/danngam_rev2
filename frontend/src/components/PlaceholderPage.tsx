interface PlaceholderPageProps {
  title: string
  screenId: string
  description?: string
}

export default function PlaceholderPage({ title, screenId, description }: PlaceholderPageProps) {
  return (
    <div className="flex flex-col items-center justify-center min-h-96 gap-4 text-center p-8">
      <div className="w-16 h-16 rounded-full bg-primary-100 flex items-center justify-center">
        <span className="text-primary-600 text-2xl">🌾</span>
      </div>
      <div>
        <h2 className="text-xl font-semibold text-gray-800">{title}</h2>
        <p className="text-sm text-gray-400 mt-1">{screenId}</p>
      </div>
      <p className="text-gray-500 text-sm max-w-sm">
        {description ?? '이 화면은 현재 개발 중입니다. Lv1 구현 예정.'}
      </p>
      <span className="px-3 py-1 bg-amber-100 text-amber-700 text-xs rounded-full">
        TODO: Lv1 구현 예정
      </span>
    </div>
  )
}
