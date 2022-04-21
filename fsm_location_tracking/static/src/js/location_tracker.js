//$(document).on('change', '#checkbox-comp-14', function() {
////$( "#checkbox-comp-14" ).change(function() {
// console.log("geo...ready!!!!")
//  if ("geolocation" in navigator) {
//      navigator.geolocation.getCurrentPosition(function(position) {
//       var lati = position.coords.latitude;
//       var longi = position.coords.longitude;
//       console.log("my", lati, longi)
//        $.ajax({
//          url: '/get_location_lati_longi',
//          type: 'GET',
//          data: {
//            latitude: lati,
//            longitude: longi
//          },
//          success: function() {},
//        });
//      });
//    } else {
//      console.log("Browser doesn't support geolocation!");
//    }
//});
   function myDoneBtn1() {
   if ("geolocation" in navigator) {
      navigator.geolocation.getCurrentPosition(function(position) {
       var lati = position.coords.latitude;
       var longi = position.coords.longitude;
       var task_id = $("span[name='id']").text();
       console.log("idssssssssss", task_id)
        $.ajax({
          url: '/get_location_lati_longi',
          type: 'GET',
          data: {
            latitude: lati,
            longitude: longi,
            task_id: task_id
          },
          success: function() {
           location.reload();
          },
        });
      });
    } else {
      console.log("Browser doesn't support geolocation!");
    }
  }

  function myDoneBtn2() {
   if ("geolocation" in navigator) {
      navigator.geolocation.getCurrentPosition(function(position) {
        var lati = position.coords.latitude;
        var longi = position.coords.longitude;
        console.log("my", lati, longi)
        $.ajax({
          url: '/get_location_lati_longi',
          type: 'GET',
          data: {
            latitude: lati,
            longitude: longi
          },
          success: function() {},
        });
      });
    } else {
      console.log("Browser doesn't support geolocation!");
    }
  }
