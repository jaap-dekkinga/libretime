const mysql = require('mysql2/promise');

async function readFingerprintBlob() {
  const connection = await mysql.createConnection({
    host: 'tuneurl.cf7k7uoervmz.us-east-2.rds.amazonaws.com',
    user: 'admin',
    password: '6PDhN4in7dFHbY',
    database: 'test',
  });

  try {
    const [rows] = await connection.execute(
      'SELECT * FROM fingerprint WHERE id=?  order by id desc limit 1',
      ['363']
    );
    console.log('Query executed successfully.', 'Rows returned:', rows);
    if (rows.length === 0) {
      console.log('No record found with id = 363');
      return;
    }

    const row = rows[0];
    const rowId = row.id;

    const blobValue = row.fingerprint;

    if (!Buffer.isBuffer(blobValue)) {
      console.log('Column "fingerprint" is not a BLOB or is null.');
      return;
    }

    const uint8Array = new Uint8Array(blobValue.buffer, blobValue.byteOffset, blobValue.byteLength);
    const trimmed = uint8Array.slice(4); // Strips the original first 4 bytes (255, 2, 2, 1)
    console.log('Column "fingerprint" (BLOB) as Uint8Array (first 4 bytes removed):');
    console.log(trimmed);
    console.log(`Length: ${trimmed.length} bytes`);

    // const header = new Uint8Array([0, 0, 0, 4]);
    // const withHeader = new Uint8Array(header.length + trimmed.length);
    // withHeader.set(header, 0);
    // withHeader.set(trimmed, header.length);
    // console.log('Final Uint8Array with new header [0, 0, 0, 4] prepended:');
    // console.log(withHeader);
    // console.log(`Length: ${withHeader.length} bytes`);

    const trimmedBuffer = Buffer.from(trimmed);
    const [result] = await connection.execute(
      'UPDATE fingerprint SET `fingerprint` = ? WHERE id = ?',
      [trimmedBuffer, rowId]
    );
    console.log(`Updated column "fingerprint" for id=${rowId}. Affected rows: ${result.affectedRows}`);
  } finally {
    await connection.end();
  }
}

readFingerprintBlob().catch(console.error);
