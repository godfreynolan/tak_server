// Complete Cot Payload

let cot_payload = {
   "event": {
       "_attributes": {
           "version": "2.0",
           "uid": uid,
           "type": cotType,
           "how": "m-g",
           "time": new Date(Date.now()).toISOString(),
           "start": new Date(Date.now()).toISOString(),
           "stale": new Date(Date.now() + (10 * 60 * 1000)).toISOString() // 10 minute period
       },
       "point": {
           "_attributes": {
               "lat": lat,
               "lon": lon,
               "hae": hae,
               "ce": "9999999",
               "le": "9999999"
           }
       },
       "detail": {
           "usericon": {
               "_attributes": { "iconsetpath": iconsetpath }
           },
           "contact": {
               "_attributes": { callsign: callsign }
           },
           "track": {
               "_attributes": {
                   speed: speed,
                   course: course
               }
           },
           "remarks": `Remote ID UAS | Operator ${operator}`,
       }
   },
}

