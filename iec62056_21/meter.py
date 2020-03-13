import logging
import datetime
from logging.config import DictConfigurator
from contextlib import contextmanager
from iec62056_21.client import Iec6205621Client
from iec62056_21 import lis200
from amr_um.models import NewMeterReading
from amr_um.schemas import NewMeterReadingSchema
import marshmallow

logger = logging.getLogger(__name__)


class GenericLis200Meter:

    """
    Generic Implementation of a LIS 200 Meter
    """

    SUPPLIER_LOCK_STATUS_ADDRESS = "3:0170.0"
    SUPPLIER_LOCK_OPEN_ADDRESS = "3:0171.0"
    CUSTOMER_LOCK_STATUS_ADDRESS = "4:0170.0"
    CUSTOMER_LOCK_OPEN_ADDRESS = "4:0171.0"
    UTC_OFFSET_ADDRESS = "1:40F.0"
    CLOCK_ADDRESS = "1:0400.0"

    VALID_ACCESS_LEVELS = ["supplier", "customer"]

    def __init__(
        self,
        name,
        protocol_address,
        host,
        port,
        protocol_password,
        access_level="supplier",
        battery_power=True,
    ):
        self.name = name
        self.protocol_address = protocol_address
        self.protocol_password = protocol_password
        self.host = host
        self.port = port
        self.access_level = access_level
        self.battery_power = battery_power

        self.client = Iec6205621Client.with_tcp_transport(
            address=(self.host, self.port),
            device_address=self.protocol_address,
            password=protocol_password,
            error_parser_class=lis200.Lis200ErrorParser,
        )

        self._utc_offset = None

    @contextmanager
    def session(self):
        """
        LIS200 does not use the standard password challange procedure as defined in IEC62056-21
        Instead they use different kinds of locks in the meter device and to do certain
        actions you need to open the appropriate lock. It is also recommended to close
        the lock after you are done.
        :return:
        """
        logger.info(f"Starting meter session for meter {self!r}")
        self.client.connect()
        password_challange = self.client.access_programming_mode()
        # We just ignore the password challange.
        self._open_lock()
        yield self
        self._close_lock()
        self.client.send_break()
        self.client.disconnect()
        logger.info("Meter session terminated.")

    def read_single_value(self, address):
        """
        Read of single value by address.

        """
        logger.info(f"Reading single value: {address}")
        response = self.client.read_single_value(address=address)
        return response

    def read_archive_by_date(
        self, start_date, end_date=None, archive_number=3, control_position=3
    ):
        """
        Enables reading an archive between two points in time. If no end_date is
        provided the end date is assumed to be the latest entry in the archive.
        Good for one-off reads.

        :param start_date:
        :param end_date:
        :param archive_number:
        :param control_position:
        :return: List(ArchiveDataPoints)
        """
        start = lis200.format_datetime(start_date)
        if end_date:
            end = lis200.format_datetime(end_date)
        else:
            end = ""

        response = self.read_archive(
            start=start,
            end=end,
            archive_number=archive_number,
            control_position=control_position,
        )

        return response.data

    def read_archive_by_offset_seconds(
        self, offset_seconds, archive_number=3, control_position=3
    ):
        """
        Enables to read the archive from the current point in time (in the meter)
        and backwards during a set of seconds.
        Since the meters time might be different than calling system the current time
        of the meter is controlled and the read is done from that point.
        Good to use with periodical reads.

        :param offset_seconds:
        :param archive_number:
        :param control_position:
        :return:
        """
        logger.info(
            f"Reading archive {archive_number} using position {control_position} from "
            f"the last {offset_seconds} seconds"
        )

        response = self.read_single_value(self.CLOCK_ADDRESS)
        device_time = lis200.parse_datetime(response.value)  # no need to use utc offset
        read_from = device_time - datetime.timedelta(seconds=offset_seconds)
        response = self.read_archive_by_date(start_date=read_from)
        return response

    def read_archive(
        self, start, end="", archive_number=3, control_position=3, datetime_position=3
    ):
        """
        Will read a LIS200 archive. Will read header data to set the address and units
        of values.

        :param start:
        :param end:
        :param archive_number:
        :param control_position:
        :param datetime_position:
        :return:
        """
        address_command = lis200.ArchiveReadoutCommand(
            archive=archive_number,
            position=control_position,
            attribute="4",
            start=start,
            end=end,
            partial_blocks=True,
        )
        logger.info(f"Reading archive header for addresses.")
        self.client.transport.send(address_command.to_bytes())
        addresses_response = self.client.read_response()

        unit_command = lis200.ArchiveReadoutCommand(
            archive=archive_number,
            position=control_position,
            attribute="3",
            start=start,
            end=end,
            partial_blocks=True,
        )
        logger.info(f"Reading archive header for units")
        self.client.transport.send(unit_command.to_bytes())
        units_response = self.client.read_response()

        values_command = lis200.ArchiveReadoutCommand(
            archive=archive_number,
            position=control_position,
            attribute="0",
            start=start,
            end=end,
            partial_blocks=True,
        )
        logger.info(f"Reading archive content.")
        self.client.transport.send(values_command.to_bytes())
        values_response = self.client.read_response()

        readout = lis200.ArchiveReadout(
            values=values_response,
            addresses=addresses_response,
            units=units_response,
            datetime_position=datetime_position,
            utc_offset=self.utc_offset,
        )

        return readout

    def set_time(self):
        """
        This function does not yet handle meters that use winter/summer time changeover.
        :return:
        """
        utc_now = datetime.datetime.utcnow()
        time_to_send = utc_now + datetime.timedelta(seconds=self.utc_offset)
        self._set_time(time_to_send)

    def _set_time(self, date_time):
        date_to_send = lis200.format_datetime(date_time)
        logger.info(f"Setting time in meter to: {date_to_send}")
        resp = self.client.write_single_value(
            address=self.CLOCK_ADDRESS, data=date_to_send
        )

    def _open_lock(self):
        """
        A lock is opened by writing to the open address. But if you write to it when it
        is closed you update the lock code.
        """
        if self._is_locked:
            logger.info(f"Opening lock")
            self.client.write_single_value(
                address=self._lock_open_address, data=self.protocol_password
            )

    def _close_lock(self):
        if not self._is_locked:
            logger.info(f"Closing lock")
            self.client.write_single_value(address=self._lock_status_address, data="0")

    @property
    def _is_locked(self):
        logger.info(f"Checking lock status")
        response = self.client.read_single_value(
            address=self._lock_status_address, additional_data="1"
        )
        lock_status = response.value
        if lock_status == "0":
            logger.info(f"Lock is closed")
            return True
        elif lock_status == "1":
            logger.info(f"Lock is open")
            return False
        else:
            raise ValueError(
                f"Received value:{lock_status} as lock status that is not a valid "
                f"response"
            )

    @property
    def _lock_status_address(self):
        if self.access_level == "supplier":
            return self.SUPPLIER_LOCK_STATUS_ADDRESS
        else:
            return self.CUSTOMER_LOCK_STATUS_ADDRESS

    @property
    def _lock_open_address(self):
        if self.access_level == "supplier":
            return self.SUPPLIER_LOCK_OPEN_ADDRESS
        else:
            return self.CUSTOMER_LOCK_OPEN_ADDRESS

    @property
    def utc_offset(self):
        """
        Will read the UTC offset of the meter and cache it for future use. Offset is
        stored in minutes in the meter, but it is more common to use seconds in python.
        """

        if not self._utc_offset:
            logger.info(f"Reading the UTC offset of the meter.")
            offset_response = self.client.read_single_value(
                address=self.UTC_OFFSET_ADDRESS
            )
            offset_min = int(offset_response.value)
            offset_seconds = offset_min * 60
            self._utc_offset = offset_seconds

        return self._utc_offset

    def make_meter_readings(self, archive_data_points):
        """
        Return proper object to put on meter readings queue
        """

        meter_readings = list()
        for data_point in archive_data_points:

            meter_reading = NewMeterReading(
                meter=self.name,
                series=data_point.address,
                timestamp=data_point.timestamp,
                value=data_point.value,
            )
            meter_readings.append(meter_reading)

        return meter_readings

    def __repr__(self):
        return (
            f"{self.__class__.__name__}(protocol_address={self.protocol_address!r}, "
            f'protocol_password="<redacted>", '
            f"host={self.host!r}, "
            f"port={self.port!r}, "
            f"access_level={self.access_level!r}, "
            f"battery_power={self.battery_power!r})"
        )


if __name__ == "__main__":
    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "filters": {},
            "formatters": {
                "main_formatter": {
                    "format": "[{asctime}] :: [{levelname}] :: {name} :: {message}",
                    "style": "{",
                }
            },
            "handlers": {
                "console": {
                    "level": "DEBUG",
                    "filters": [],
                    "class": "logging.StreamHandler",
                    "formatter": "main_formatter",
                }
            },
            "loggers": {"": {"handlers": ["console"], "level": "DEBUG"}},
        }
    )

    connection_settings = {
        "type": "serial",
        "settings": {"port": "/dev/tty.usbserial-A61CNFK2"},
    }

    meter = GenericLis200Meter(
        name="MyMeter",
        protocol_address="",
        host="10.70.138.159",
        port=4059,
        protocol_password="00000000",
    )

    with meter.session() as meter:
        resp = meter.read_archive_by_offset_seconds(offset_seconds=10000)

        meter.set_time()
        resp2 = meter.read_single_value(address="1:40F.0")
        mr = meter.make_meter_readings(resp)
        # print(resp.data)
    # print(resp)
    # print(resp2)

    for m in mr:
        try:
            print(NewMeterReadingSchema().dump(m))
        except marshmallow.exceptions.ValidationError:
            print("not valid")

    print(len(mr))
