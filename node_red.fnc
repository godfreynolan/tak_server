// Complete Function

const lat = msg.payload.location.latitude
const lon = msg.payload.location.longitude
const hae = msg.payload.location.altitude_m
const callsign = msg.payload.uas_id
const uid = `UAS - ${ callsign }`
const iconsetpath = "34ae1613-9645-4222-a9d2-e5f243dea286/Military/Air/UAS"
// Common CoT type for UAV / air track; adjust if your TAK conventions differ:
// "a-f-A-M-F-Q" is often used for friendly aircraft(UAV fits many setups).
const cotType = "a-f-A-M-F-Q"
const speed = msg.payload.velocity.ground_speed_mps
const course = msg.payload.velocity.heading_deg
const operator = msg.payload.operator_id


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

msg.payload = cot_payload
return msg;

