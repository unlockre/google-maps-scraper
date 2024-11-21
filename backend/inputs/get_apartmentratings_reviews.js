/**
 * @typedef {import('../../frontend/node_modules/botasaurus-controls/dist/index').Controls} Controls
 */


/**
 * @param {Controls} controls
 */
function getInput(controls) {
    controls
        .link('url', {
            placeholder: "https://www.apartmentratings.com/ga/jonesboro/villas-by-the-lake_678817444130328/",
            label: 'Property URL',
            isRequired: true
        })
}