import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { ChakraProvider, extendTheme, ColorModeScript } from '@chakra-ui/react'
import App from './App.jsx'

import './index.css'

// 1. Define a theme configuration
const config = {
  initialColorMode: 'dark', // Set default to dark mode
  useSystemColorMode: false, // Don't use system preference for now, enforce dark
}

// 2. Extend the theme (can add custom colors, fonts later)
const theme = extendTheme({
  config, // Pass the config
  styles: {
    global: (props) => ({ // Global styles
      body: {
        bg: props.colorMode === 'dark' ? 'gray.800' : 'gray.50', // Darker background for dark mode
        color: props.colorMode === 'dark' ? 'whiteAlpha.900' : 'gray.800',
      },
    }),
  },
  colors: { // Example: Add a brand color
    brand: {
      50: '#e6fffa',  // Lightest teal
      100: '#b2f5ea',
      200: '#81e6d9',
      300: '#4fd1c5',
      400: '#38b2ac',
      500: '#319795', // Main brand teal
      600: '#2c7a7b',
      700: '#285e61',
      800: '#234e52',
      900: '#1d4044', // Darkest teal
    },
    // You can add more custom palettes here, e.g., for player pieces
    playerX: { // Example: A soft orange/red
      500: '#DD6B20', // Chakra orange.600
      text: '#FFFFFF'
    },
    playerO: { // Example: A distinct blue
      500: '#3182CE', // Chakra blue.500
      text: '#FFFFFF'
    }
  },
  components: { // Example: Override default component styles
    Button: {
      baseStyle: {
        fontWeight: 'bold',
      },
      variants: {
        solid: (props) => ({ // Customize solid buttons
          bg: props.colorMode === 'dark' ? 'brand.500' : 'brand.500',
          color: 'white',
          _hover: {
            bg: props.colorMode === 'dark' ? 'brand.600' : 'brand.600',
          },
        }),
      },
    },
  },
})

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <ColorModeScript initialColorMode={theme.config.initialColorMode} />
    <ChakraProvider theme={theme}>
      <App />
    </ChakraProvider>
  </StrictMode>,
)
