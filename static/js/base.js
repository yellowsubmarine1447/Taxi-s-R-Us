/* This whole js file is only linked in index.html */

/* This section here puts a placeholder value in the fare form */

let today = new Date();
let time = (today.getHours()<10?'0':'') + today.getHours() + ":" + (today.getMinutes()<10?'0':'') + today.getMinutes()
let timeField = document.getElementById("trip_time");
let dateField = document.getElementById("trip_date");
let month = today.getMonth() + 1;
timeField.value = time;
dateField.value = today.getFullYear() + "-" + (month<10?'0':'') + month + "-" + (today.getDate()<10?'0':'') + today.getDate();

/* This section here attaches the Bing Maps Auto-Suggest onto the origin and destination input fields. The code is
* a modified version of a sample UI (https://www.bing.com/api/maps/sdk/mapcontrol/isdk/autosuggestui#HTML). As you can
* see, a lot of features have been removed, such as the map. */
function GetSuggestions() {
    Microsoft.Maps.loadModule('Microsoft.Maps.AutoSuggest', {
        callback: function () {
            var manager1 = new Microsoft.Maps.AutosuggestManager({placeSuggestions: false});
            manager1.attachAutosuggest('#origin', '#originContainer');
            var manager2 = new Microsoft.Maps.AutosuggestManager({placeSuggestions: false});
            manager2.attachAutosuggest('#destination', '#destinationContainer');
        }
    });
}

/* And that's it! */