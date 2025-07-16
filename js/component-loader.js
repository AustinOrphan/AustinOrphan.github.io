/**
 * Component Loader System
 * Dynamically loads HTML components into the main page
 */

class ComponentLoader {
    constructor() {
        this.components = [
            { name: 'about', target: 'about-container', path: 'components/about.html' },
            { name: 'projects', target: 'projects-container', path: 'components/projects.html' },
            { name: 'contact', target: 'contact-container', path: 'components/contact.html' },
            { name: 'footer', target: 'footer-container', path: 'components/footer.html' }
        ];
        this.loadedComponents = new Set();
    }

    /**
     * Load a single component
     * @param {Object} component - Component configuration
     * @returns {Promise} - Promise that resolves when component is loaded
     */
    async loadComponent(component) {
        try {
            // Check if we're in a file:// context
            if (window.location.protocol === 'file:') {
                throw new Error('CORS restriction: Components require HTTP server');
            }
            
            const response = await fetch(component.path);
            if (!response.ok) {
                throw new Error(`Failed to load ${component.name}: ${response.statusText}`);
            }
            
            const html = await response.text();
            const container = document.getElementById(component.target);
            
            if (container) {
                container.innerHTML = html;
                this.loadedComponents.add(component.name);
                
                // Dispatch custom event for component loaded
                window.dispatchEvent(new CustomEvent('componentLoaded', { 
                    detail: { name: component.name } 
                }));
                
                console.log(`Component ${component.name} loaded successfully`);
            } else {
                console.error(`Container ${component.target} not found`);
            }
        } catch (error) {
            console.error(`Error loading component ${component.name}:`, error);
            // Fallback: show error message in container
            const container = document.getElementById(component.target);
            if (container) {
                container.innerHTML = `
                    <div class="component-error">
                        <p>⚠️ ${component.name} section unavailable</p>
                        <p style="font-size: 0.9em; opacity: 0.8;">Use local server for full functionality</p>
                    </div>
                `;
            }
        }
    }

    /**
     * Load all components
     * @returns {Promise} - Promise that resolves when all components are loaded
     */
    async loadAllComponents() {
        const loadPromises = this.components.map(component => this.loadComponent(component));
        await Promise.all(loadPromises);
        
        // Dispatch event when all components are loaded
        window.dispatchEvent(new Event('allComponentsLoaded'));
        
        // Re-initialize any scripts that depend on the loaded content
        this.reinitializeScripts();
    }

    /**
     * Re-initialize scripts after components are loaded
     */
    reinitializeScripts() {
        // Re-initialize form validation if contact form is loaded
        if (this.loadedComponents.has('contact')) {
            if (typeof initializeContactForm === 'function') {
                initializeContactForm();
            }
        }

        // Re-initialize footer functionality if footer is loaded
        if (this.loadedComponents.has('footer')) {
            if (typeof initializeFooter === 'function') {
                initializeFooter();
            }
        }

        // Re-initialize scroll animations
        if (typeof initializeScrollAnimations === 'function') {
            initializeScrollAnimations();
        }

        // Re-initialize navigation active states
        if (typeof updateActiveNavigation === 'function') {
            updateActiveNavigation();
        }

        // Dispatch event for custom initialization
        window.dispatchEvent(new Event('componentsReinitialized'));
    }

    /**
     * Check if a component is loaded
     * @param {string} componentName - Name of the component
     * @returns {boolean} - True if component is loaded
     */
    isComponentLoaded(componentName) {
        return this.loadedComponents.has(componentName);
    }
}

// Initialize component loader when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    const loader = new ComponentLoader();
    
    // Load all components
    loader.loadAllComponents().then(() => {
        console.log('All components loaded successfully');
    }).catch(error => {
        console.error('Error loading components:', error);
    });

    // Expose loader instance globally for debugging
    window.componentLoader = loader;
});