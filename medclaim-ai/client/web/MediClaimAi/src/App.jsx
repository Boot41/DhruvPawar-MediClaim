import { useState } from 'react'
import reactLogo from './assets/react.svg'
import viteLogo from '/vite.svg'

function App() {
  const [count, setCount] = useState(0)

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center">
      <div className="max-w-md mx-auto bg-white rounded-xl shadow-lg p-8 text-center">
        <div className="flex justify-center space-x-4 mb-8">
          <a href="https://vite.dev" target="_blank" className="hover:opacity-80 transition-opacity">
            <img src={viteLogo} className="h-16 w-16" alt="Vite logo" />
          </a>
          <a href="https://react.dev" target="_blank" className="hover:opacity-80 transition-opacity">
            <img src={reactLogo} className="h-16 w-16 animate-spin" alt="React logo" />
          </a>
        </div>
        
        <h1 className="text-3xl font-bold text-gray-800 mb-8">MediClaim AI</h1>
        
        <div className="bg-gray-50 rounded-lg p-6 mb-6">
          <button 
            onClick={() => setCount((count) => count + 1)}
            className="bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 px-6 rounded-lg transition-colors duration-200 shadow-md hover:shadow-lg"
          >
            Count is {count}
          </button>
          <p className="mt-4 text-gray-600">
            Edit <code className="bg-gray-200 px-2 py-1 rounded text-sm">src/App.jsx</code> and save to test HMR
          </p>
        </div>
        
        <p className="text-sm text-gray-500">
          Tailwind CSS is now configured! 🎉
        </p>
        
        <div className="mt-6 flex justify-center space-x-2">
          <span className="inline-block w-3 h-3 bg-blue-500 rounded-full"></span>
          <span className="inline-block w-3 h-3 bg-green-500 rounded-full"></span>
          <span className="inline-block w-3 h-3 bg-purple-500 rounded-full"></span>
        </div>
      </div>
    </div>
  )
}

export default App
