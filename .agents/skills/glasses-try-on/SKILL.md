---
name: glasses-try-on
description: Find distinctive eyeglass frames, save reference images, and create try-on images from the user's face photos in the style project. Use when the user asks to shortlist frames or visualize frames on their photos.
---

# Glasses frame search and try-on

Help the user compare several expressive, elegant frames with a deliberately bold, slightly nerdy character. The glasses are for appearance only; do not discuss prescriptions or vision correction unless the user asks.

## Project context

- Treat every image in `resources/faces/` as a read-only original. Use only the photos the user selects.
- Save selected frame reference images in `resources/frames/`. Add or update `resources/frames/SOURCES.md` with the model or product name, maker or seller, source page, and direct image URL when available.
- Save generated try-ons in `resources/try-ons/`; never overwrite face photos or frame references with generated results.
- Keep the person's identity, facial features, facial hair, expression, lighting, background, and crop consistent with each base photo. Change only the glasses, adapting fit and perspective to the photo.

## Workflow

1. List the files in `resources/faces/` and `resources/frames/`. Ask the user interactively with `AskUserQuestion`, in one call with two multi-select questions:
   - **Faces**: which photos to use (one option per file, plus "All").
   - **Frames**: which existing references to try on (one option per file, plus "Search for new frames").
   Since a question allows at most four options, ask in batches or let the user answer via "Other" when there are more files. Skip a question whose folder is empty and treat that as "search for new frames". Do not proceed until both are answered.
2. Inspect the selected face photos and frame references. Note whether any photo is unsuitable for a particular angle.
3. If the user chose to search, search current product listings or reliable maker pages for at least three clearly different frame directions, such as round or panto, geometric or rectangular, and bold acetate. Choose specific models and colors based on the user's goal, not trendiness alone. Prefer product images with a clear front or slight-angle view and no model's face obscuring the frame.
4. Save usable frame reference images under `resources/frames/`. Keep their filenames descriptive. Record source details and links in `SOURCES.md`; distinguish source product images from generated imagery. If an image cannot be saved or its use is restricted, explain that and choose another usable reference.
5. For each selected frame and each selected face photo, generate a separate try-on with `uv run style try-on <face> <frame>`, for example `uv run style try-on resources/faces/003-IMG-1447.jpeg resources/frames/002-cubitts-polygon-sage.jpg`. The command picks the provider from the environment (`OPENROUTER_API_KEY`, then `GEMINI_API_KEY`, then `OPENAI_API_KEY`); if it exits with an error, report it and fall back to any other available image-generation capability. Preserve the original photo and do not add other accessories or retouch facial features.
6. The command saves results to `resources/try-ons/<face>__<frame>.png`, named after the input files. Use the same naming for any fallback output.
7. Summarize the selected frames, why each fits the requested style, links to sources, output locations, and any combinations that could not be generated. If useful, compare the strongest options across the frontal and three-quarter views. Make short videos only when the user asks.

Do not make unrelated code changes or run tests for this image-selection task. Do not present generated try-ons as photographs of the real products or as photographs taken by the user.
