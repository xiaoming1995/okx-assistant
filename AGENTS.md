# OKX Dashboard Collaboration Guide

## Frontend design standard

Before changing any user-visible frontend code, stylesheet, component structure, interaction, or responsive behavior under `frontend/`, read and follow [docs/frontend-design-guidelines.md](docs/frontend-design-guidelines.md).

The guide is the authoritative UI baseline for this repository. Keep the product's simple, tool-oriented style; do not introduce a new visual language or arbitrary spacing, color, elevation, or motion values without first updating that guide and explaining the reason in the related change.

When a frontend change is complete, verify the changed state at the relevant desktop and narrow-width breakpoints, including loading, empty, error/cache, keyboard-focus, and disabled states where applicable.
