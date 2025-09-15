import { ImageResponse } from 'next/og'

// Route segment config
// export const runtime = 'edge' // Disabled for production build stability

// Image metadata
export const size = {
  width: 32,
  height: 32,
}
export const contentType = 'image/png'

// Image generation
export default function Icon() {
  return new ImageResponse(
    (
      <div
        style={{
          background: 'linear-gradient(135deg, #fb923c 0%, #ea580c 100%)',
          width: '100%',
          height: '100%',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          borderRadius: '6px',
        }}
      >
        {/* Palm/Hand icon */}
        <svg
          width="20"
          height="20"
          viewBox="0 0 24 24"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
        >
          <path
            d="M18 11V6a2 2 0 0 0-2-2v0a2 2 0 0 0-2 2v5m4 0V9a2 2 0 0 0-2-2v0a2 2 0 0 0-2 2v2m4 0V9a2 2 0 0 0-2-2v0a2 2 0 0 0-2 2v2m0 0V7a2 2 0 0 0-2-2v0a2 2 0 0 0-2 2v4m8 0v4a6 6 0 0 1-6 6H8a6 6 0 0 1-6-6v-1c0-.27.02-.54.06-.8A2 2 0 0 1 4 13h1"
            stroke="white"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            fill="white"
            fillOpacity="0.9"
          />
        </svg>
      </div>
    ),
    {
      ...size,
    }
  )
}