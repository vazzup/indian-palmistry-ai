import { ImageResponse } from 'next/og'

// Route segment config
export const runtime = 'edge'

// Image metadata
export const size = {
  width: 180,
  height: 180,
}
export const contentType = 'image/png'

// Image generation
export default function AppleIcon() {
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
          borderRadius: '22px',
        }}
      >
        {/* Palm/Hand icon - larger for apple touch icon */}
        <svg
          width="100"
          height="100"
          viewBox="0 0 24 24"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
        >
          <path
            d="M18 11V6a2 2 0 0 0-2-2v0a2 2 0 0 0-2 2v5m4 0V9a2 2 0 0 0-2-2v0a2 2 0 0 0-2 2v2m4 0V9a2 2 0 0 0-2-2v0a2 2 0 0 0-2 2v2m0 0V7a2 2 0 0 0-2-2v0a2 2 0 0 0-2 2v4m8 0v4a6 6 0 0 1-6 6H8a6 6 0 0 1-6-6v-1c0-.27.02-.54.06-.8A2 2 0 0 1 4 13h1"
            stroke="white"
            strokeWidth="1.5"
            strokeLinecap="round"
            strokeLinejoin="round"
            fill="white"
            fillOpacity="0.95"
          />
          {/* Add some palm lines for authenticity */}
          <path
            d="M8 16c1-1 2-1 3 0M8 18c1.5-0.5 2.5-0.5 4 0"
            stroke="white"
            strokeWidth="1"
            strokeLinecap="round"
            opacity="0.7"
          />
        </svg>
      </div>
    ),
    {
      ...size,
    }
  )
}